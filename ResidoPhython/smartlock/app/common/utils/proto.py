from google.protobuf.json_format import MessageToDict


class ProtoUtils:
    @classmethod
    def to_dict(cls, proto_obj):
        if proto_obj is None:
            return {}

        return MessageToDict(proto_obj)
