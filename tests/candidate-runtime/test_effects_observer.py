import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location("effects_harness",Path(__file__).with_name("run_candidate.py"))
h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
def sample():
    return {"tables":{"CARGO":{"rows":1,"sha256":"a"*64}},"queues":{name:{attribute:0 for attribute in h.QUEUE_ATTRIBUTES} for name in h.REQUIRED_QUEUES},"business_invocations":{"read":1}}
class Clock:
    def __init__(self):self.now=0
    def clock(self):return self.now
    def pause(self,seconds):self.now+=seconds
class EffectsObserverTests(unittest.TestCase):
    def test_missing_terminal_queue_fails_instead_of_empty_pass(self):
        value=sample();del value["queues"]["jms.queue.DLQ"]
        with self.assertRaises(RuntimeError):h.validate_effects(value)
    def test_empty_or_malformed_independent_channels_fail(self):
        for channel in ["tables","queues","business_invocations"]:
            value=sample();value[channel]={}
            with self.subTest(channel=channel),self.assertRaises(RuntimeError):h.validate_effects(value)
        value=sample();value["tables"]["CARGO"]["sha256"]="unhashed"
        with self.assertRaises(RuntimeError):h.validate_effects(value)
    def test_enqueue_then_consume_resets_settlement_even_at_zero_depth(self):
        before=sample();after=copy.deepcopy(before)
        after["queues"]["jms.queue.CargoHandledQueue"]["MessagesAdded"]=1
        after["queues"]["jms.queue.CargoHandledQueue"]["MessagesAcknowledged"]=1
        samples=iter([before,before,after,after,after]);clock=Clock()
        self.assertEqual(h.settle_effects(lambda:next(samples),clock=clock.clock,pause=clock.pause),after)
        self.assertEqual(clock.now,2)
    def test_same_row_count_replacement_resets_settlement(self):
        before=sample();after=copy.deepcopy(before);after["tables"]["CARGO"]["sha256"]="b"*64
        samples=iter([before,before,after,after,after]);clock=Clock()
        self.assertEqual(h.settle_effects(lambda:next(samples),clock=clock.clock,pause=clock.pause),after)
        self.assertEqual(clock.now,2)
    def test_unsettled_or_negative_counters_never_pass(self):
        value=sample();value["queues"]["jms.queue.CargoHandledQueue"]["DeliveringCount"]=1
        clock=Clock()
        with self.assertRaises(RuntimeError):h.settle_effects(lambda:value,timeout=2,clock=clock.clock,pause=clock.pause)
        value["queues"]["jms.queue.CargoHandledQueue"]["MessagesAdded"]=-1
        with self.assertRaises(RuntimeError):h.validate_effects(value)
if __name__=="__main__":unittest.main()
