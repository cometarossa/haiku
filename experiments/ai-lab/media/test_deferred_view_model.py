"""Executable design model for one pending latest-frame notification."""
import itertools
import unittest


class ViewModel:
    def __init__(self):
        self.latest = None
        self.pending = False
        self.queued = False
        self.drawn = []

    def publish(self, value, delivery=True):
        self.latest = value
        if value is None or self.pending:
            return
        self.pending = True
        if delivery:
            self.queued = True
        else:
            self.pending = False
            # Existing synchronous fallback, under the bitmap lock.
            self.draw_current()

    def draw_current(self):
        if self.latest is not None:
            self.drawn.append(self.latest)

    def handle(self, concurrent=None):
        if not self.queued:
            return
        self.queued = False
        # Reservation released BEFORE acquiring the latest bitmap.
        self.pending = False
        if concurrent is not None:
            self.publish(concurrent)
        self.draw_current()


class DeferredViewModelTest(unittest.TestCase):
    def test_coalesce(self):
        m = ViewModel()
        for i in range(100):
            m.publish(i)
        self.assertTrue(m.queued)
        m.handle()
        self.assertEqual(m.drawn, [99])
        self.assertFalse(m.pending)

    def test_clear_before_draw(self):
        m = ViewModel()
        m.publish(1)
        m.handle(concurrent=2)
        self.assertTrue(m.queued)
        m.handle()
        self.assertEqual(m.drawn, [2, 2])
        self.assertFalse(m.pending)

    def test_null_does_not_draw_stale_pointer(self):
        m = ViewModel()
        m.publish(1)
        m.publish(None)
        m.handle()
        self.assertEqual(m.drawn, [])
        m.publish(2)
        m.handle()
        self.assertEqual(m.drawn, [2])

    def test_failed_delivery_fallback(self):
        m = ViewModel()
        m.publish(1, delivery=False)
        self.assertEqual(m.drawn, [1])
        self.assertFalse(m.pending)
        m.publish(2)
        m.handle()
        self.assertEqual(m.drawn, [1, 2])

    def test_sequential_interleavings(self):
        for ops in itertools.product(("publish", "fail", "stop", "handle"), repeat=6):
            m = ViewModel()
            for i, op in enumerate(ops):
                if op == "publish":
                    m.publish(i)
                elif op == "fail":
                    m.publish(i, delivery=False)
                elif op == "stop":
                    m.publish(None)
                else:
                    m.handle()
                self.assertEqual(m.pending, m.queued)
            m.handle()
            self.assertFalse(m.pending)
            if m.latest is not None:
                self.assertEqual(m.drawn[-1], m.latest)
