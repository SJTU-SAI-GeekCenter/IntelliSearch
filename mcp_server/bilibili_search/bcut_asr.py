import requests
import logging
import time
from os import PathLike
from pathlib import Path
from typing import Literal, Optional
from enum import Enum
from pydantic import BaseModel
import re
from urllib.parse import urlparse, parse_qs

INFILE_FMT = ["flac", "aac", "m4a", "mp3", "wav"]
OUTFILE_FMT = ["srt", "json", "lrc", "txt"]

__version__ = "0.0.3"

API_BASE_URL = "https://member.bilibili.com/x/bcut/rubick-interface"

# 申请上传
API_REQ_UPLOAD = API_BASE_URL + "/resource/create"

# 提交上传
API_COMMIT_UPLOAD = API_BASE_URL + "/resource/create/complete"

# 创建任务
API_CREATE_TASK = API_BASE_URL + "/task"

# 查询结果
API_QUERY_RESULT = API_BASE_URL + "/task/result"

SUPPORT_SOUND_FORMAT = Literal["flac", "aac", "m4a", "mp3", "wav", "mp4", "m4s"]

INFILE_FMT = ["flac", "aac", "m4a", "mp3", "wav", "mp4", "m4s"]
OUTFILE_FMT = ["srt", "json", "lrc", "txt"]

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Cache-Control": "no-cache"
}

def get_audio_subtitle(url: str):
    asr = BcutASR(file=url)
    try:
        task_id = asr.create_task()
        while True:
            task_resp = asr.result(task_id)
            match task_resp.state:
                case ResultStateEnum.ERROR:
                    return APIError(task_resp.code, task_resp.msg)
                case ResultStateEnum.COMPLETE:
                    return task_resp.parse().to_txt()
                
            time.sleep(5)
    except Exception as e:
        return APIError(400, str(e) or "获取音频字幕失败")

class APIError(Exception):
    "接口调用错误"

    def __init__(self, code, msg) -> None:
        self.code = code
        self.msg = msg
        super().__init__()

    def __str__(self) -> str:
        return f"{self.code}:{self.msg}"


class ASRDataSeg(BaseModel):
    """文字识别-断句"""

    class ASRDataWords(BaseModel):
        """文字识别-逐字"""

        label: str
        start_time: int
        end_time: int

    start_time: int
    end_time: int
    transcript: str
    words: list[ASRDataWords]

    def to_srt_ts(self) -> str:
        """转换为srt时间戳"""

        def _conv(ms: int) -> tuple[int, int, int, int]:
            return ms // 3600000, ms // 60000 % 60, ms // 1000 % 60, ms % 1000

        s_h, s_m, s_s, s_ms = _conv(self.start_time)
        e_h, e_m, e_s, e_ms = _conv(self.end_time)
        return f"{s_h:02d}:{s_m:02d}:{s_s:02d},{s_ms:03d} --> {e_h:02d}:{e_m:02d}:{e_s:02d},{e_ms:03d}"

    def to_lrc_ts(self) -> str:
        """转换为lrc时间戳"""

        def _conv(ms: int) -> tuple[int, int, int]:
            return ms // 60000, ms // 1000 % 60, ms % 1000 // 10

        s_m, s_s, s_ms = _conv(self.start_time)
        return f"[{s_m:02d}:{s_s:02d}.{s_ms:02d}]"


class ASRData(BaseModel):
    """语音识别结果"""

    utterances: list[ASRDataSeg]
    version: str

    def __iter__(self):
        return iter(self.utterances)

    def has_data(self) -> bool:
        """是否识别到数据"""
        return len(self.utterances) > 0

    def to_txt(self) -> str:
        """转成 txt 格式字幕 (无时间标记)"""
        return "".join(seg.transcript for seg in self.utterances)

    def to_srt(self) -> str:
        """转成 srt 格式字幕"""
        return "\n".join(
            f"{n}\n{seg.to_srt_ts()}\n{seg.transcript}\n"
            for n, seg in enumerate(self.utterances, 1)
        )

    def to_lrc(self) -> str:
        """转成 lrc 格式字幕"""
        return "\n".join(
            f"{seg.to_lrc_ts()}{seg.transcript}" for seg in self.utterances
        )

    def to_ass(self) -> str:
        """转换为 ass 格式"""
        # TODO: ass 序列化实现
        raise NotImplementedError


class ResourceCreateRspSchema(BaseModel):
    """上传申请响应"""

    resource_id: str
    title: str
    type: int
    in_boss_key: str
    size: int
    upload_urls: list[str]
    upload_id: str
    per_size: int


class ResourceCompleteRspSchema(BaseModel):
    """上传提交响应"""

    resource_id: str
    download_url: str


class TaskCreateRspSchema(BaseModel):
    """任务创建响应"""

    resource: str
    result: str
    task_id: str  # 任务id


class ResultStateEnum(Enum):
    """任务状态枚举"""

    STOP = 0  # 未开始
    RUNING = 1  # 运行中
    ERROR = 3  # 错误
    COMPLETE = 4  # 完成


class ResultRspSchema(BaseModel):
    """任务结果查询响应"""

    task_id: str  # 任务id
    result: str  # 结果数据-json
    remark: str  # 任务状态详情
    state: ResultStateEnum  # 任务状态

    def parse(self) -> ASRData:
        "解析结果数据"
        return ASRData.model_validate_json(self.result)


class BcutASR:
    "必剪 语音识别接口"
    session: requests.Session
    sound_name: str
    sound_url: str
    sound_bin: bytes
    sound_fmt: SUPPORT_SOUND_FORMAT
    __in_boss_key: str
    __resource_id: str
    __upload_id: str
    __upload_urls: list[str]
    __per_size: int
    __clips: int
    __etags: list[str]
    __download_url: str
    task_id: str

    def __init__(self, file: Optional[str | PathLike] = None) -> None:
        self.session = requests.Session()
        self.task_id = None
        self.__etags = []
        if file:
            self.set_data(file)

    def set_data(
        self,
        file: Optional[str | PathLike] = None,
        raw_data: Optional[bytes] = None,
        data_fmt: Optional[SUPPORT_SOUND_FORMAT] = None,
    ) -> None:
        "设置欲识别的数据"
        if file:
            if not isinstance(file, (str, PathLike)):
                raise TypeError("unknow file ptr")
            
            if re.match(r'^https?://', file):
                self.sound_url = file
                # 使用 urlparse 解析 URL
                parsed_url = urlparse(file)
                
                # 获取后缀名的优先级：
                # 1. 用户指定的 data_fmt
                # 2. URL 路径中的后缀
                # 3. 默认使用 m4s（B站音频格式）
                if data_fmt:
                    suffix = data_fmt
                else:
                    path = parsed_url.path.split('/')[-1]  # 获取文件名部分
                    if '.' in path:
                        suffix = path.split('.')[-1]
                    else:
                        suffix = 'm4s'  # B站默认音频格式
                
                self.sound_name = f'audio.{suffix}'
                self.__download_url = file
            else:
                # 文件类
                file = Path(file)
                self.sound_bin = open(file, "rb").read()
                suffix = data_fmt or file.suffix[1:]
                self.sound_name = file.name
        elif raw_data:
            # bytes类
            self.sound_bin = raw_data
            suffix = data_fmt
            self.sound_name = f"{int(time.time())}.{suffix}"
        else:
            raise ValueError("none set data")
        if suffix not in SUPPORT_SOUND_FORMAT.__args__:
            raise TypeError(f"format {suffix} is not support")
        self.sound_fmt = suffix
        logging.info(f"加载文件成功: {self.sound_name}")

    def upload(self) -> None:
        "申请上传"
        if not self.sound_bin or not self.sound_fmt or not self.sound_url:
            raise ValueError("none set data")
        resp = self.session.post(
            API_REQ_UPLOAD,
            data={
                "type": 2,
                "name": self.sound_name,
                "size": len(self.sound_bin),
                "resource_file_type": self.sound_fmt,
                "model_id": '8',
            },
            headers=headers,
        )
        resp.raise_for_status()
        resp = resp.json()
        code = resp["code"]
        if code:
            raise APIError(code, resp["message"])
        resp_data = ResourceCreateRspSchema.parse_obj(resp["data"])
        self.__in_boss_key = resp_data.in_boss_key
        self.__resource_id = resp_data.resource_id
        self.__upload_id = resp_data.upload_id
        self.__upload_urls = resp_data.upload_urls
        self.__per_size = resp_data.per_size
        self.__clips = len(resp_data.upload_urls)
        logging.info(
            f"申请上传成功, 总计大小{resp_data.size // 1024}KB, {self.__clips}分片, 分片大小{resp_data.per_size // 1024}KB: {self.__in_boss_key}"
        )
        self.__upload_part()
        self.__commit_upload()

    def __upload_part(self) -> None:
        "上传音频数据"
        for clip in range(self.__clips):
            start_range = clip * self.__per_size
            end_range = (clip + 1) * self.__per_size
            logging.info(f"开始上传分片{clip}: {start_range}-{end_range}")
            resp = self.session.put(
                self.__upload_urls[clip],
                data=self.sound_bin[start_range:end_range],
                headers=headers,
            )
            resp.raise_for_status()
            etag = resp.headers.get("Etag")
            self.__etags.append(etag)
            logging.info(f"分片{clip}上传成功: {etag}")

    def __commit_upload(self) -> None:
        "提交上传数据"
        resp = self.session.post(
            API_COMMIT_UPLOAD,
            data={
                "in_boss_key": self.__in_boss_key,
                "resource_id": self.__resource_id,
                "etags": ",".join(self.__etags),
                "upload_id": self.__upload_id,
                "model_id": "8",
            },
            headers=headers,
        )
        resp.raise_for_status()
        resp = resp.json()
        code = resp["code"]
        if code:
            raise APIError(code, resp["message"])
        resp_data = ResourceCompleteRspSchema.model_validate(resp["data"])
        self.__download_url = resp_data.download_url
        logging.info(f"提交成功")

    def create_task(self) -> str:
        "开始创建转换任务"
        resp = self.session.post(
            API_CREATE_TASK, json={"resource": self.__download_url, "model_id": "8"},
            headers=headers,
        )
        resp.raise_for_status()
        resp = resp.json()
        code = resp["code"]
        if code:
            raise APIError(code, resp["message"])
        resp_data = TaskCreateRspSchema.model_validate(resp["data"])
        self.task_id = resp_data.task_id
        logging.info(f"任务已创建: {self.task_id}")
        return self.task_id

    def result(self, task_id: Optional[str] = None) -> ResultRspSchema:
        "查询转换结果"
        resp = self.session.get(
            API_QUERY_RESULT, params={"model_id": "8", "task_id": task_id or self.task_id},headers=headers,
        )
        resp.raise_for_status()
        resp = resp.json()
        code = resp["code"]
        if code:
            raise APIError(code, resp["message"])
        return ResultRspSchema.model_validate(resp["data"])
