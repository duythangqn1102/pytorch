from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

from caffe2.python import core, workspace
from hypothesis import given
import caffe2.python.hypothesis_test_util as hu
import hypothesis.strategies as st
import numpy as np


class TestElementwiseOps(hu.HypothesisTestCase):

    @given(n=st.integers(0, 6), m=st.integers(4, 6),
           seed=st.integers(0, 1000), **hu.gcs)
    def test_log(self, n, m, gc, dc, seed):
        np.random.seed(seed)
        X = np.random.rand(n, m).astype(np.float32) + 1.0

        def log_op(X):
            return [np.log(X)]

        op = core.CreateOperator(
            "Log",
            ["X"],
            ["Z"]
        )

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X],
            reference=log_op,
        )

        self.assertGradientChecks(
            gc, op, [X], 0, [0], stepsize=1e-4, threshold=1e-2)

    @given(n=st.integers(0, 10), m=st.integers(4, 6),
           d=st.integers(2, 3), seed=st.integers(0, 1000), **hu.gcs)
    def test_powt(self, n, m, d, gc, dc, seed):
        np.random.seed(seed)
        X = np.random.rand(n, m, d).astype(np.float32) + 1.0
        Y = np.random.rand(n, m, d).astype(np.float32) + 2.0

        def powt_op(X, Y):
            return [np.power(X, Y)]

        #two gradients Y*X^(Y-1) and X^Y * ln(X)
        def powt_grad(g_out, outputs, fwd_inputs):
            [X, Y] = fwd_inputs
            Z = outputs[0]
            return ([Y * np.power(X, Y - 1), Z * np.log(X)] * g_out)

        op = core.CreateOperator(
            "Pow",
            ["X", "Y"],
            ["Z"]
        )

        self.assertReferenceChecks(device_option=gc,
                                   op=op,
                                   inputs=[X, Y],
                                   reference=powt_op,
                                   output_to_grad="Z",
                                   grad_reference=powt_grad)

    @given(n=st.integers(0, 6), m=st.integers(4, 6),
           seed=st.integers(0, 1000), **hu.gcs)
    def test_sqr(self, n, m, gc, dc, seed):
        np.random.seed(seed)
        X = np.random.rand(n, m).astype(np.float32)

        def sqr_op(X):
            return [np.square(X)]

        op = core.CreateOperator(
            "Sqr",
            ["X"],
            ["Z"]
        )

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X],
            reference=sqr_op,
        )

        self.assertGradientChecks(
            gc, op, [X], 0, [0], stepsize=1e-4, threshold=1e-2)

    @given(
        X=hu.tensor(
            elements=st.floats(0.1, 10),
            # allow empty tensor
            min_value=0),
        inplace=st.booleans(),
        **hu.gcs
    )
    def test_sqrt(self, X, inplace, gc, dc):
        def sqrt_op(X):
            return [np.sqrt(X)]

        op = core.CreateOperator(
            "Sqrt",
            ["X"],
            ["X"] if inplace else ["Y"]
        )

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X],
            reference=sqrt_op,
        )
        self.assertDeviceChecks(dc, op, [X], [0])
        # stepsize need to be smaller than the possible minimum X, so the
        # sqrt is well defined
        self.assertGradientChecks(
            gc, op, [X], 0, [0], stepsize=1e-2)

    @given(X=hu.tensor(elements=st.floats(0.1, 10.0), dtype=np.float32),
           inplace=st.booleans(), **hu.gcs)
    def test_rsqrt(self, X, inplace, gc, dc):
        op = core.CreateOperator(
            "RSqrt",
            ["X"],
            ["X"] if inplace else ["Y"],
        )

        def rsqrt_ref(X):
            return [1.0 / np.sqrt(X)]

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X],
            reference=rsqrt_ref,
        )
        self.assertDeviceChecks(dc, op, [X], [0])
        self.assertGradientChecks(gc, op, [X], 0, [0], stepsize=5e-3)

    @given(n=st.integers(0, 6), m=st.integers(4, 6),
           seed=st.integers(0, 1000), **hu.gcs)
    def test_swish(self, n, m, gc, dc, seed):
        np.random.seed(seed)
        X = np.random.rand(n, m).astype(np.float32)

        def swish(X):
            return [np.divide(X, (1. + np.exp(-X)))]

        op = core.CreateOperator(
            "Swish",
            ["X"],
            ["Z"]
        )

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X],
            reference=swish,
        )

        self.assertGradientChecks(
            gc, op, [X], 0, [0], stepsize=1e-4, threshold=1e-2)

    @given(n=st.integers(0, 6), m=st.integers(4, 6),
           seed=st.integers(0, 1000), **hu.gcs)
    def test_swish_gradient_inplace(self, n, m, gc, dc, seed):
        np.random.seed(seed)

        def swish(X):
            return [np.divide(X, (1. + np.exp(-X)))]

        def swish_gradient(X, Y, dY):
            return [dY * (Y + np.divide(1. - Y, 1. + np.exp(-X)))]

        X = np.random.rand(n, m).astype(np.float32)
        Y = swish(X)[0]
        dY = np.random.rand(n, m).astype(np.float32)
        op = core.CreateOperator(
            "SwishGradient",
            ["X", "Y", "grad"],
            "grad"
        )

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X, Y, dY],
            reference=swish_gradient,
        )

    @given(n=st.integers(0, 6), m=st.integers(4, 6),
           seed=st.integers(0, 1000), **hu.gcs)
    def test_sigmoid(self, n, m, gc, dc, seed):
        np.random.seed(seed)
        X = np.random.rand(n, m).astype(np.float32)

        def sigmoid(X):
            return [1. / (1. + np.exp(-X))]

        op = core.CreateOperator(
            "Sigmoid",
            ["X"],
            ["Z"]
        )

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X],
            reference=sigmoid,
        )

        self.assertGradientChecks(
            gc, op, [X], 0, [0], stepsize=1e-4, threshold=1e-2)

    @given(n=st.integers(0, 6), m=st.integers(4, 6), **hu.gcs)
    def test_eq(self, n, m, gc, dc):
        # Set broadcast and no axis, i.e. broadcasting last dimensions.
        X = np.random.randint(2, size=(n, m))
        Y = np.random.randint(2, size=(n, m))
        op = core.CreateOperator("EQ", ["X", "Y"], "out", broadcast=1)

        def eq(X, Y):
            return [X == Y]

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X, Y],
            reference=eq,
        )

        workspace.FeedBlob('X', X)
        workspace.FeedBlob('Y', Y)

        net = core.Net("batch_bucket_one_hot_test")
        result = net.EQ(["X", "Y"], 1)
        (shapes, types) = workspace.InferShapesAndTypes([net])
        workspace.RunNetOnce(net)

        self.assertEqual(shapes[result], list(workspace.blobs[result].shape))
        self.assertEqual(shapes[result], list(X.shape))
        self.assertEqual(types[result], core.DataType.BOOL)

    @given(n=st.integers(0, 6), m=st.integers(4, 6), **hu.gcs)
    def test_eq_bcast(self, n, m, gc, dc):
        # Set broadcast and no axis, i.e. broadcasting last dimensions.
        X = np.random.randint(2, size=(n, m))
        Y = np.random.randint(2, size=(m,))
        op = core.CreateOperator("EQ", ["X", "Y"], "out", broadcast=1)

        def eq(X, Y):
            return [X == Y]

        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=[X, Y],
            reference=eq,
        )

        workspace.FeedBlob('X', X)
        workspace.FeedBlob('Y', Y)

        net = core.Net("eq_bast")
        result = net.EQ(["X", "Y"], 1, broadcast=1)
        (shapes, types) = workspace.InferShapesAndTypes([net])
        workspace.RunNetOnce(net)
        self.assertTrue(str(result) in shapes)
        self.assertEqual(shapes[result], list(workspace.blobs[result].shape))
        self.assertEqual(shapes[result], list(X.shape))
        self.assertEqual(types[result], core.DataType.BOOL)

        net_2 = core.Net("eq_bast_invalid")
        result_2 = net_2.EQ(["X", "Y"], 1)
        (shapes, types) = workspace.InferShapesAndTypes([net])
        self.assertTrue(str(result_2) not in shapes)

    def _run_single_test(self, op, ref, A, B, test_grad, gc, dc):
        inputs = [A, B]
        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=inputs,
            reference=ref,
        )
        self.assertDeviceChecks(dc, op, inputs, [0])
        if test_grad:
            for i in range(len(inputs)):
                self.assertGradientChecks(gc, op, inputs, i, [0])

        inputs = [B, A]
        self.assertReferenceChecks(
            device_option=gc,
            op=op,
            inputs=inputs,
            reference=ref,
        )
        self.assertDeviceChecks(dc, op, inputs, [0])
        if test_grad:
            for i in range(len(inputs)):
                self.assertGradientChecks(gc, op, inputs, i, [0])

    def _test_binary_op(
            self, op_name, np_ref, n, m, k, t, bias, test_grad, gc, dc):
        op = core.CreateOperator(
            op_name,
            ["A", "B"],
            ["C"],
        )

        def ref(A, B):
            return [np_ref(A, B)]

        A = np.random.rand(n, m, k, t).astype(np.float32) + bias
        B = np.random.rand(n, m, k, t).astype(np.float32) + bias
        self._run_single_test(op, ref, A, B, test_grad, gc, dc)

        A = np.random.rand(1).astype(np.float32) + bias
        B = np.random.rand(n, m, k, t).astype(np.float32) + bias
        self._run_single_test(op, ref, A, B, test_grad, gc, dc)

        A = np.random.rand(k, t).astype(np.float32) + bias
        B = np.random.rand(n, m, k, t).astype(np.float32) + bias
        self._run_single_test(op, ref, A, B, test_grad, gc, dc)

        A = np.random.rand(n, m, 1, 1).astype(np.float32) + bias
        B = np.random.rand(n, m, k, t).astype(np.float32) + bias
        self._run_single_test(op, ref, A, B, test_grad, gc, dc)

        A = np.random.rand(m, 1, t).astype(np.float32) + bias
        B = np.random.rand(n, m, k, t).astype(np.float32) + bias
        self._run_single_test(op, ref, A, B, test_grad, gc, dc)

        A = np.random.rand(1, m, 1, t).astype(np.float32) + bias
        B = np.random.rand(n, 1, k, 1).astype(np.float32) + bias
        self._run_single_test(op, ref, A, B, test_grad, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_add(self, n, m, k, t, gc, dc):
        self._test_binary_op("Add", np.add, n, m, k, t, -0.5, True, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_sub(self, n, m, k, t, gc, dc):
        self._test_binary_op("Sub", np.subtract, n, m,
                             k, t, -0.5, True, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_mul(self, n, m, k, t, gc, dc):
        self._test_binary_op("Mul", np.multiply, n, m,
                             k, t, -0.5, True, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_div(self, n, m, k, t, gc, dc):
        self._test_binary_op("Div", np.divide, n, m, k, t, 1.0, True, gc, dc)

    def _test_bitwise_binary_op(self, op_name, np_ref, n, m, k, t, gc, dc):
        op = core.CreateOperator(
            op_name,
            ["A", "B"],
            ["C"],
        )

        def ref(A, B):
            return [np_ref(A, B)]

        A = np.random.randint(128, size=(n, m, k, t))
        B = np.random.randint(128, size=(n, m, k, t))
        self._run_single_test(op, ref, A, B, False, gc, dc)

        A = np.random.randint(128, size=1)
        B = np.random.randint(128, size=(n, m, k, t))
        self._run_single_test(op, ref, A, B, False, gc, dc)

        A = np.random.randint(128, size=(k, t))
        B = np.random.randint(128, size=(n, m, k, t))
        self._run_single_test(op, ref, A, B, False, gc, dc)

        A = np.random.randint(128, size=(n, m, 1, 1))
        B = np.random.randint(128, size=(n, m, k, t))
        self._run_single_test(op, ref, A, B, False, gc, dc)

        A = np.random.randint(128, size=(m, 1, t))
        B = np.random.randint(128, size=(n, m, k, t))
        self._run_single_test(op, ref, A, B, False, gc, dc)

        A = np.random.randint(128, size=(1, m, 1, t))
        B = np.random.randint(128, size=(n, 1, k, 1))
        self._run_single_test(op, ref, A, B, False, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_bitwise_and(self, n, m, k, t, gc, dc):
        self._test_bitwise_binary_op(
            "BitwiseAnd", np.bitwise_and, n, m, k, t, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_bitwise_or(self, n, m, k, t, gc, dc):
        self._test_bitwise_binary_op(
            "BitwiseOr", np.bitwise_or, n, m, k, t, gc, dc)

    @given(n=st.integers(1, 5), m=st.integers(1, 5), k=st.integers(1, 5),
           t=st.integers(1, 5), **hu.gcs)
    def test_bitwise_xor(self, n, m, k, t, gc, dc):
        self._test_bitwise_binary_op(
            "BitwiseXor", np.bitwise_xor, n, m, k, t, gc, dc)
