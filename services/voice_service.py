from typing import Optional, Dict, Any
import asyncio
import numpy as np
from pathlib import Path
import torch
import torchaudio
from TTS.api import TTS
from faster_whisper import WhisperModel
from utils.logger import get_logger
import uuid
import os

voice_logger = get_logger('voice')

class VoiceService:
    def __init__(self):
        """初始化语音服务"""
        self._whisper_model = None
        self._tts_model = None
        self.voice_samples: Dict[str, Path] = {}
        voice_logger.info("语音服务初始化完成")
    
    async def save_voice_config(self, config: Dict[str, Any], sample_path: str) -> None:
        """保存语音配置和样本"""
        try:
            voice_name = config["name"]
            self.voice_samples[voice_name] = Path(sample_path)
            voice_logger.info(f"语音配置已保存: {voice_name}")
        except Exception as e:
            voice_logger.error(f"保存语音配置失败: {str(e)}")
            raise
    
    async def get_voice_configs(self):
        """获取所有保存的语音配置"""
        try:
            voice_logger.info("开始获取语音配置...")
            # 构建配置列表
            configs = []
            
            # 添加默认语音配置
            configs.append({
                "name": "default",
                "language": "multilingual",
                "description": "默认多语言语音模型",
                "type": "default"
            })
            
            # 添加用户克隆的语音配置
            for user_id, sample_path in self.voice_samples.items():
                configs.append({
                    "name": user_id,
                    "language": "multilingual",
                    "description": f"用户 {user_id} 的克隆语音",
                    "type": "cloned",
                    "sample_path": str(sample_path)
                })
            
            voice_logger.info(f"获取到 {len(configs)} 个语音配置")
            return configs
        except Exception as e:
            voice_logger.error(f"获取语音配置失败: {str(e)}")
            raise
    
    @property
    def whisper_model(self):
        """懒加载 Whisper 模型"""
        if self._whisper_model is None:
            try:
                device = "cpu"  # 强制使用 CPU 以避免 CUDA 内存问题
                voice_logger.info(f"正在加载 Whisper 模型，设备: {device}")
                # 使用较小的模型以减少内存使用
                self._whisper_model = WhisperModel("small", device=device, compute_type="int8")
                voice_logger.info("Whisper 模型加载完成")
            except Exception as e:
                voice_logger.error(f"加载 Whisper 模型失败: {str(e)}")
                raise
        return self._whisper_model
    
    @property
    def tts_model(self):
        """懒加载 TTS 模型"""
        if self._tts_model is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
            voice_logger.info(f"正在加载 TTS 模型，设备: {device}")
            self._tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
        return self._tts_model
    
    async def transcribe_audio(self, audio_data: bytes) -> str:
        """将音频转写为文本"""
        try:
            voice_logger.info("开始音频转写...")
            
            # 保存音频到临时文件
            temp_file = Path("temp") / f"temp_{uuid.uuid4()}.wav"
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                # 如果是 webm 格式，需要先转换为 wav
                temp_webm = Path("temp") / f"temp_{uuid.uuid4()}.webm"
                with open(temp_webm, "wb") as f:
                    f.write(audio_data)
                
                # 使用 ffmpeg 转换格式，添加错误检查
                voice_logger.info("正在将音频转换为 wav 格式...")
                result = os.system(f'ffmpeg -i {temp_webm} -acodec pcm_s16le -ar 16000 {temp_file} 2>/dev/null')
                if result != 0:
                    raise ValueError("音频转换失败")
                
                if not temp_file.exists() or temp_file.stat().st_size == 0:
                    raise ValueError("音频转换后的文件无效")
                
                # 使用 Whisper 模型进行转写
                voice_logger.info("正在使用 Whisper 模型进行转写...")
                segments, _ = self.whisper_model.transcribe(str(temp_file), beam_size=1)
                
                # 获取转写结果
                text = " ".join([segment.text for segment in segments])
                voice_logger.info(f"转写完成: {text}")
                
                return text
                
            finally:
                # 清理临时文件
                if temp_webm.exists():
                    temp_webm.unlink()
                if temp_file.exists():
                    temp_file.unlink()
            
        except Exception as e:
            voice_logger.error(f"音频转写失败: {str(e)}")
            raise
    
    async def clone_voice(self, user_id: str, audio_path: str) -> bool:
        """
        克隆用户声音
        """
        try:
            voice_dir = Path("voices") / user_id
            voice_dir.mkdir(parents=True, exist_ok=True)
            target_path = voice_dir / "reference.wav"
            
            # 确保音频格式正确
            audio, sr = torchaudio.load(audio_path)
            if sr != 16000:
                resampler = torchaudio.transforms.Resample(sr, 16000)
                audio = resampler(audio)
            torchaudio.save(target_path, audio, 16000)
            
            self.voice_samples[user_id] = target_path
            voice_logger.info(f"声音克隆成功: {user_id}")
            return True
        except Exception as e:
            voice_logger.error(f"声音克隆失败: {str(e)}")
            return False
    
    async def text_to_speech(self, text: str, user_id: Optional[str] = None) -> str:
        """
        将文本转换为语音
        """
        try:
            output_path = Path("voices") / "temp" / f"{hash(text)}.wav"
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if user_id and user_id in self.voice_samples:
                # 使用克隆的声音
                self.tts_model.tts_to_file(
                    text=text,
                    file_path=str(output_path),
                    speaker_wav=str(self.voice_samples[user_id])
                )
                voice_logger.info(f"使用克隆声音生成语音: {user_id}")
            else:
                # 使用默认声音
                self.tts_model.tts_to_file(
                    text=text,
                    file_path=str(output_path)
                )
                voice_logger.info("使用默认声音生成语音")
            
            return str(output_path)
        except Exception as e:
            voice_logger.error(f"语音生成失败: {str(e)}")
            return ""
    
    async def detect_voice_activity(self, audio_data: np.ndarray, sample_rate: int = 16000) -> bool:
        """
        检测语音活动
        """
        try:
            # 简单的能量检测方法
            energy = np.mean(audio_data ** 2)
            threshold = 0.01  # 可调整的阈值
            is_active = energy > threshold
            voice_logger.debug(f"语音活动检测: {'活跃' if is_active else '静默'}")
            return is_active
        except Exception as e:
            voice_logger.error(f"语音活动检测失败: {str(e)}")
            return False
    
    async def cleanup(self):
        """清理资源"""
        try:
            # 清理临时文件
            temp_dir = Path("voices") / "temp"
            if temp_dir.exists():
                for file in temp_dir.glob("*.wav"):
                    file.unlink()
            voice_logger.info("临时文件清理完成")
        except Exception as e:
            voice_logger.error(f"清理失败: {str(e)}") 
    
    async def synthesize_voice(self, text: str, voice_name: str) -> bytes:
        """使用指定的语音配置合成语音"""
        try:
            voice_logger.info(f"开始语音合成，文本: {text}, 音色: {voice_name}")
            
            # 获取语音模型
            device = "cuda" if torch.cuda.is_available() else "cpu"
            if self._tts_model is None:
                voice_logger.info(f"正在加载 TTS 模型，设备: {device}")
                self._tts_model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(device)
            
            # 获取语音样本路径
            sample_path = None
            if voice_name != "default":
                sample_path = self.voice_samples.get(voice_name)
                if not sample_path:
                    raise ValueError(f"找不到语音配置: {voice_name}")
                if not sample_path.exists():
                    raise ValueError(f"找不到语音样本文件: {sample_path}")
                voice_logger.info(f"使用语音样本: {sample_path}")
            
            # 合成语音
            temp_file = Path("temp") / f"temp_{uuid.uuid4()}.wav"
            temp_file.parent.mkdir(parents=True, exist_ok=True)
            
            voice_logger.info("开始合成语音...")
            if sample_path:
                self._tts_model.tts_to_file(
                    text=text,
                    file_path=str(temp_file),
                    speaker_wav=str(sample_path),
                    language="zh"  # 默认使用中文
                )
            else:
                self._tts_model.tts_to_file(
                    text=text,
                    file_path=str(temp_file),
                    language="zh"  # 默认使用中文
                )
            
            voice_logger.info("语音合成完成，正在读取音频数据...")
            
            # 读取合成的音频数据
            with open(temp_file, "rb") as f:
                audio_data = f.read()
            
            # 删除临时文件
            temp_file.unlink()
            
            voice_logger.info(f"语音合成完成: {voice_name}")
            return audio_data
        except Exception as e:
            voice_logger.error(f"语音合成失败: {str(e)}")
            raise
    
    async def edit_voice_config(self, config: Dict[str, Any]) -> None:
        """编辑语音配置"""
        try:
            voice_name = config["name"]
            if voice_name not in self.voice_samples:
                raise ValueError(f"找不到语音配置: {voice_name}")
            
            # 更新配置
            self.voice_samples[voice_name] = self.voice_samples[voice_name]
            voice_logger.info(f"语音配置已更新: {voice_name}")
        except Exception as e:
            voice_logger.error(f"更新语音配置失败: {str(e)}")
            raise
    
    async def delete_voice_config(self, voice_name: str) -> None:
        """删除语音配置"""
        try:
            if voice_name not in self.voice_samples:
                raise ValueError(f"找不到语音配置: {voice_name}")
            
            # 删除音频文件
            sample_path = self.voice_samples[voice_name]
            if sample_path.exists():
                sample_path.unlink()
            
            # 删除配置
            del self.voice_samples[voice_name]
            voice_logger.info(f"语音配置已删除: {voice_name}")
        except Exception as e:
            voice_logger.error(f"删除语音配置失败: {str(e)}")
            raise 