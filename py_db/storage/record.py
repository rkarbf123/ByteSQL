import struct


class RecordSerializer:
    @staticmethod
    def serialize(row, columns):
        fmt = "<"
        data = []
        for val, col in zip(row, columns):
            col_type = col["type"]
            if col_type == "INT":
                fmt += "i"
                data.append(int(val))
            elif col_type == "TEXT":
                encoded = str(val).encode("utf-8")
                fmt += f"I{len(encoded)}s"
                data.append(len(encoded))
                data.append(encoded)
        return struct.pack(fmt, *data)

    @staticmethod
    def deserialize(bytes_data, columns):
        row = []
        offset = 0
        for col in columns:
            col_type = col["type"]
            if col_type == "INT":
                val = struct.unpack_from("<i", bytes_data, offset)[0]
                row.append(val)
                offset += 4
            elif col_type == "TEXT":
                length = struct.unpack_from("<I", bytes_data, offset)[0]
                offset += 4
                val = struct.unpack_from(f"<{length}s", bytes_data, offset)[0]
                row.append(val.decode("utf-8"))
                offset += length
        return tuple(row), offset