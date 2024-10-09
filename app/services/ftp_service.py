from ftplib import FTP
from app.config import settings
from app.utils.utils import logger
from collections import defaultdict

class FTPService:
    def __init__(self):
        self.host = settings.FTP_HOST
        self.user = settings.FTP_USER
        self.password = settings.FTP_PASSWORD

    def connect(self):
        try:
            ftp = FTP(self.host)
            ftp.login(user=self.user, passwd=self.password)
            return ftp
        except Exception as e:
            logger.error(f"Ошибка при подключении к FTP серверу: {str(e)}")
            raise

    def get_image_links(self):
        ftp = self.connect()
        try:
            files = []
            ftp.retrlines('LIST', files.append)

            grouped_images = defaultdict(list)
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif')):
                    filename = file.split()[-1]
                    parts = filename.split('_')
                    if len(parts) == 2:
                        article = parts[0]
                        grouped_images[article].append(filename)

            return grouped_images
        except Exception as e:
            logger.error(f"Ошибка при получении списка изображений: {str(e)}")
            raise
        finally:
            ftp.quit()

    def get_image(self, filename):
        ftp = self.connect()
        try:
            image_data = bytearray()
            ftp.retrbinary(f'RETR {filename}', image_data.extend)
            return image_data
        except Exception as e:
            logger.error(f"Ошибка при получении изображения {filename}: {str(e)}")
            raise
        finally:
            ftp.quit()

ftp_service = FTPService()
