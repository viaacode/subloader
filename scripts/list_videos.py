from app.mediahaven_api import MediahavenApi

mh_api = MediahavenApi()
result = mh_api.list_videos()


# print(f"result={result}")

print(f"videos={result['totalNrOfResults']}")

for v in result['mediaDataList']:
    print(f"pid={v['externalId']}  file={v['originalFileName']}")
    print(f"file={v['externalId']}")


# should output now:
# python list_videos.py
# videos=4
# pid=974e1a33f35c474f841ec18fdb3efa93d6abf9a1029f44d9aaa9275f643576d0b2d2cdbc4e5745c89a46a443422995aa
# pid=qs5d8ncx8c
# pid=qsxs5jbm5c
# pid=qsf7664p39
