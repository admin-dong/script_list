# 引入模块
from obs import ObsClient
from obs import PutObjectHeader




access_key_id='',  #AK
secret_access_key='',  #SK
server=''   #桶的链接域名
# 创建ObsClient实例
obsClient = ObsClient(
    access_key_id=access_key_id,
    secret_access_key=secret_access_key,
    server=server
)
bucketName='test'  #桶的名字



#创建一个obs类 并传递桶名字参数
class obspull(object):
    def __init__(self,bucketName):
        self.bucketName = bucketName

    #创建文件夹
    def CreateObsDirctory(self,obsdirctory):
        try:
            # 在文件夹下创建对象
            resp = obsClient.putContent(self.bucketName, obsdirctory, content=None)

            if resp.status < 300:
                print('requestId:', resp.requestId)
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
        except:
            import traceback

            print(traceback.format_exc())


     #上传文件
    def pushfile(self,objectKey,file_path):
        try:


            headers = PutObjectHeader()
            headers.contentType = 'text/plain'

            resp = obsClient.putFile(self.bucketName,objectKey, file_path)

            if resp.status < 300:
                print('requestId:', resp.requestId)
                print('etag:', resp.body.etag)
                print('versionId:', resp.body.versionId)
                print('storageClass:', resp.body.storageClass)
            else:
                print('errorCode:', resp.errorCode)
                print('errorMessage:', resp.errorMessage)
        except:
            import traceback
            print(traceback.format_exc())





pushobsdir = 'eolink_report/test.zip'  #要上传到obs的目录文件
sourcedir = '/usr/local/cv2x/report/test.zip'  #本地文件及路径

pullclass = obspull(bucketName)
pullclass.CreateObsDirctory('eolink_report/2023-08-25/')   #创建文件夹
pullclass.pushfile(pushobsdir,sourcedir)   #上传文件

obsClient.close()