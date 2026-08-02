import bcrypt

stored_hash = "$2a$06$42qM7a9NmV1aY1Z3cV6T5.nufMD0.pdXYTxnQnmDX9CDkIoKSlPZa"
result = bcrypt.checkpw("123456".encode("utf-8"), stored_hash.encode("utf-8"))
print(result)