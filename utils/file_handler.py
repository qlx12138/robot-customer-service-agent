"""
文件处理
"""

import os
import hashlib
from utils.logger_handler import logger
from langchain_core.documents import Document
from langchain_community.document_loaders import PyPDFLoader, TextLoader


def get_file_md5_hex(file_path:str) -> str:          #获取文件的md5的十六进制字符串
    if not os.path.exists(file_path):
        logger.error(f"文件不存在: {file_path}")
        return

    if not os.path.isfile(file_path):
        logger.error(f"不是一个文件: {file_path}")
        return

    md5_obj = hashlib.md5()
    chunk_size = 4096               #设置读取文件的块大小，单位为字节,避免一次性读取过大的文件导致内存不足
    try:
        with open(file_path, 'rb') as f:         #分块模式读取必须采用二进制
            while chunk := f.read(chunk_size):
                md5_obj.update(chunk)

            md5_hex = md5_obj.hexdigest()
            return md5_hex
    except Exception as e:
        logger.error(f"计算文件md5失败: {file_path}, 错误信息: {str(e)}")
        return

def listdir_with_allowed_type(path:str, allowed_types:tuple[str]):   #列出指定目录下的所有文件，返回一个列表，列表中只包含指定类型的文件
    files = []

    if not os.path.isdir(path):
        logger.error(f"不是一个目录: {path}")
        return allowed_types

    for f in os.listdir(path):
        if f.endswith(allowed_types):
            files.append(os.path.join(path, f))

    return tuple(files)

def pdf_loader(file_path:str, password=None) -> list[Document]:                                           #加载pdf文件，返回一个pdf对象
    return PyPDFLoader(file_path, password).load()

def text_loader(file_path:str) -> list[Document]:                                          #加载文本文件，返回一个文本对象
    return TextLoader(file_path, encoding='utf-8').load()