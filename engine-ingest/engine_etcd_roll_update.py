import os
import datetime
import argparse

UpdateDays = 20
ESBackupDir = "/ingest-data/etcd-backup"

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='etcd数据库备份文件删除')
    parser.add_argument("-d", '--update_days', action="store", \
        dest="update_days", default="20", help="超限天数")
    args = parser.parse_args()

    updateDays = int(args.update_days)
    if not updateDays:
        updateDays = UpdateDays

    dateNow = datetime.datetime.now()
    dateDeadline = dateNow - datetime.timedelta(days=updateDays)

    strDeadline = dateDeadline.strftime("%Y%m%d")
    deadLineDateValue = int(strDeadline)

    for root, dirs, files in os.walk(ESBackupDir):
        for dirName in dirs:
            strDateTime = dirName.replace("-", "")
            if strDateTime.isdigit() and len(strDateTime) == 8:
                dateTimeValue = int(strDateTime)
                if dateTimeValue <= deadLineDateValue:
                    # 删除文件夹
                    backupDirPath = os.path.join(ESBackupDir, dirName)
                    cmd = f"sudo rm -rf {backupDirPath}"
                    print("Delete backup dir, execute cmd:", cmd)
                    cmdStatus = os.system(cmd)
                    if cmdStatus != 0:
                        print("Execute rm -rf cmd failed!")
                        continue

                    print("Delete succeed!")

    exit(0)