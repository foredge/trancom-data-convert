from google.cloud import storage
import os
import pdb

BUCKET_NAME = 'trancom-data-convert'

def get_file_list_from_gcs(): 
    dirs = storage.Client().list_blobs(BUCKET_NAME)
    return dirs

def file_download_and_delete_from_gcs(dir):
    file_name = dir.name.split('/')[1]
    bucket = storage.Client().get_bucket(BUCKET_NAME)
    data = bucket.blob(dir.name)
    data.download_to_filename('./logs/' + file_name)
    print("{} was downloaded.".format(file_name))

    # data.delete()
    # print("{} was deleted.".format(file_name))
    if file_name == 'test.log':
        data.delete()
        print("{} was deleted.".format(file_name))

def main():
    # gcsにアクセス
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = 'spreadsheet_service_account.json'
    dirs = get_file_list_from_gcs()
    for dir in dirs:
        file_download_and_delete_from_gcs(dir)

if __name__ == "__main__":
    main()