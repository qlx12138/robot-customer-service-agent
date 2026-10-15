"""
向量存储服务
"""

from langchain_chroma import Chroma
from utils.config_handler import chroma_conf
from model.factory import embedding_model
from langchain_text_splitters import RecursiveCharacterTextSplitter
import os
from utils.path_tool import get_abs_path
from utils.file_handler import pdf_loader, text_loader, listdir_with_allowed_type, get_file_md5_hex
from utils.logger_handler import logger
from langchain_core.documents import Document


class VectorStoreService:
    def __init__(self):
        self.vector_store = Chroma(
            collection_name=chroma_conf["collection_name"],
            embedding_function=embedding_model,
            persist_directory=get_abs_path(chroma_conf["persist_directory"])
        )

        self.spliter = RecursiveCharacterTextSplitter(
            chunk_size=chroma_conf["chunk_size"],
            chunk_overlap=chroma_conf["chunk_overlap"],
            separators=chroma_conf["separators"],
            length_function=len
        )

    def get_retriever(self):
        return self.vector_store.as_retriever(search_kwargs={'k': chroma_conf["k"]})

    def load_document(self):
        """从数据文件夹内读取数据文件，转为向量存入数据库"""
        def check_md5_hex(md5_for_check: str):
            if not os.path.exists(get_abs_path(chroma_conf["md5_hex_store"])):
                #不存在则创建文件
                open(get_abs_path(chroma_conf["md5_hex_store"]), 'w', encoding='utf-8').close()
                return False

            with open(get_abs_path(chroma_conf["md5_hex_store"]), 'r', encoding='utf-8') as f:
                for line in f.readlines():
                    line = line.strip()
                    if line == md5_for_check:
                        return True

        def save_md5_hex(md5_for_check: str):
            with open(get_abs_path(chroma_conf["md5_hex_store"]), 'a', encoding='utf-8') as f:
                f.write(md5_for_check + "\n")

        def get_file_documents(read_path: str):
            if read_path.endswith("txt"):
                return text_loader(read_path)
            if read_path.endswith("pdf"):
                return pdf_loader(read_path)
            return []

        allowed_file_path: list[str] = listdir_with_allowed_type(
            get_abs_path(chroma_conf["data_path"]),
            tuple(chroma_conf["allow_knowledge_file_type"])
        )

        for path in allowed_file_path:
            #第一步先获取文件md5值
            md5_hex = get_file_md5_hex(path)

            #第二步查重
            if check_md5_hex(md5_hex):
                logger.info(f"{path}已存在知识库中，已跳过")
                continue

            #第三步，若有有效内容则存入数据库
            try:
                documents: list[Document] = get_file_documents(path)
                if not documents:
                    logger.warning(f"{path}内没有有效文本内容，已跳过")
                    continue

                split_document: list[Document] = self.spliter.split_documents(documents)
                if not split_document:
                    logger.warning(f"{path}分片后没有有效的文本内容，已跳过")
                    continue

                self.vector_store.add_documents(split_document)
                logger.info(f"{path}内容已成功载入")

                #第四步记录存入数据的新md5值
                save_md5_hex(md5_hex)
                logger.info(f"{path}文件md5值已记录")

            except Exception as e:
                #exc_info为True会记录详细的报错堆栈，反之则只记录报错信息本身
                logger.error(f"{path}文件加载失败：{str(e)}", exc_info=True)


if __name__ == '__main__':
    vs = VectorStoreService()
    vs.load_document()
    retriever = vs.get_retriever()

    res = retriever.invoke("迷路")
    for r in res:
        print(r.page_content)
        print("="*20)