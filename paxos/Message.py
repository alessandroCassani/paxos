import PhaseMessage_pb2

class Message:
    @staticmethod
    def phase_1a(c_rnd, phase):
        msg = PhaseMessage_pb2.Phase1A()
        msg.c_rnd = c_rnd
        msg.phase = phase
        return msg.SerializeToString()

    @staticmethod
    def phase_1b(rnd, v_rnd, v_val, phase):
        msg = PhaseMessage_pb2.Phase1B()
        msg.rnd = rnd
        msg.v_rnd = v_rnd
        msg.v_val = v_val
        msg.phase = phase
        return msg.SerializeToString()

    @staticmethod
    def phase_2a(c_rnd, c_val, phase):
        msg = PhaseMessage_pb2.Phase2A()
        msg.c_rnd = c_rnd
        msg.c_val = c_val
        msg.phase = phase
        return msg.SerializeToString()

    @staticmethod
    def phase_2b(v_rnd, v_val, phase):
        msg = PhaseMessage_pb2.Phase2B()
        msg.v_rnd = v_rnd
        msg.v_val = v_val
        msg.phase = phase
        return msg.SerializeToString()

    @staticmethod
    def decision(v_val, phase):
        msg = PhaseMessage_pb2.Decide()
        msg.v_val = v_val
        msg.phase = phase
        return msg.SerializeToString()
