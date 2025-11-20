import logging
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import time

from decouple import config
from openai import OpenAI

from api.v1._shared.custom_schemas import TranscriptionResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL = "whisper-1" 
LANGUAGE = "pt"
OPENAI_API_KEY = config("OPENAI_API_KEY")

def analyze_audio_quality(audio_path: str) -> dict:
    """
    Analisa a qualidade do áudio antes da transcrição para otimizar o processamento.
    
    Args:
        audio_path: Caminho para o arquivo de áudio
        
    Returns:
        dict: Informações sobre a qualidade e características do áudio
    """
    try:
        # Comando para análise detalhada do áudio
        analysis_cmd = [
            "ffprobe",
            "-v", "quiet",
            "-select_streams", "a:0",
            "-show_entries", "stream=sample_rate,channels,duration,bit_rate:format=duration",
            "-of", "csv=p=0",
            str(audio_path)
        ]
        
        result = subprocess.run(analysis_cmd, capture_output=True, text=True, check=True)
        
        # Parse das informações (formato: sample_rate,channels,duration,bit_rate,total_duration)
        parts = result.stdout.strip().split(',')
        
        if len(parts) >= 4:
            sample_rate = int(parts[0]) if parts[0] else 0
            channels = int(parts[1]) if parts[1] else 0
            duration = float(parts[2]) if parts[2] else 0
            bit_rate = int(parts[3]) if parts[3] else 0
            
            # Calcula qualidade estimada
            quality_score = 0
            if sample_rate >= 16000: quality_score += 25
            if sample_rate >= 22050: quality_score += 15
            if sample_rate >= 44100: quality_score += 10
            if channels >= 1: quality_score += 20
            if bit_rate >= 128000: quality_score += 30
            
            return {
                "sample_rate": sample_rate,
                "channels": channels,
                "duration": duration,
                "bit_rate": bit_rate,
                "quality_score": quality_score,
                "is_suitable": quality_score >= 45,  # Mínimo para boa transcrição
                "recommended_processing": sample_rate > 16000 or channels > 1  # Precisa otimização
            }
    
    except Exception as e:
        logger.warning(f"Não foi possível analisar qualidade do áudio: {e}")
    
    return {
        "sample_rate": 0,
        "channels": 0,
        "duration": 0,
        "bit_rate": 0,
        "quality_score": 0,
        "is_suitable": True,  # Assume que é adequado se não conseguir analisar
        "recommended_processing": True
    }

def check_ffmpeg_installation():
    """
    Verifica se ffmpeg e ffprobe estão instalados e disponíveis no PATH.
    """
    missing_tools = []
    
    if not shutil.which("ffmpeg"):
        missing_tools.append("ffmpeg")
    if not shutil.which("ffprobe"):
        missing_tools.append("ffprobe")
    
    if missing_tools:
        install_instructions = """
        Para instalar o FFmpeg:
        
        Windows:
        1. Baixe de: https://www.gyan.dev/ffmpeg/builds/
        2. Extraia e adicione ao PATH do sistema
        
        macOS:
        brew install ffmpeg
        
        Linux (Ubuntu/Debian):
        sudo apt update && sudo apt install ffmpeg
        
        Linux (CentOS/RHEL):
        sudo yum install ffmpeg
        """
        raise RuntimeError(f"Ferramentas não encontradas: {', '.join(missing_tools)}\n{install_instructions}")

def transcribe_mp4_to_text(video_path: str) -> TranscriptionResult:
    """
    Extrai o áudio de um MP4 e transcreve com OpenAI, retornando objeto com detalhes.
    Requer: OPENAI_API_KEY no ambiente e ffmpeg instalado no PATH.
    
    Args:
        video_path: Caminho para o arquivo MP4
        
    Returns:
        TranscriptionResult: Objeto com texto, tokens utilizados, modelo e duração
    """
    video_path = Path(video_path)
    if not video_path.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {video_path}")

    # Verifica se ferramentas estão instaladas
    check_ffmpeg_installation()

    # Análise prévia da qualidade do áudio
    logger.info(f"Analisando qualidade do arquivo: {video_path}")
    audio_quality = analyze_audio_quality(video_path)
    
    logger.info(f"Qualidade do áudio original:")
    logger.info(f"  - Sample Rate: {audio_quality['sample_rate']} Hz")
    logger.info(f"  - Canais: {audio_quality['channels']}")
    logger.info(f"  - Bit Rate: {audio_quality['bit_rate']} bps")
    logger.info(f"  - Score de qualidade: {audio_quality['quality_score']}/100")
    logger.info(f"  - Adequado para transcrição: {'Sim' if audio_quality['is_suitable'] else 'Não'}")
    
    if not audio_quality['is_suitable']:
        logger.warning("Qualidade do áudio pode resultar em transcrição imprecisa")

    client = OpenAI(api_key=OPENAI_API_KEY)

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            audio_wav = Path(tmpdir) / "audio.wav"

            logger.info(f"Iniciando processamento otimizado de: {video_path}")
            
            # Primeiro, obtém duração do arquivo original
            duration_cmd = [
                "ffprobe",
                "-v", "quiet",
                "-show_entries", "format=duration",
                "-of", "default=noprint_wrappers=1:nokey=1",
                str(video_path)
            ]
            
            try:
                duration_result = subprocess.run(duration_cmd, capture_output=True, text=True, check=True)
                duration_seconds = float(duration_result.stdout.strip()) if duration_result.stdout.strip() else 0.0
                logger.info(f"Duração do arquivo: {duration_seconds:.2f} segundos")
            except (subprocess.CalledProcessError, ValueError) as e:
                logger.warning(f"Não foi possível obter duração do arquivo: {e}")
                duration_seconds = 0.0

            # Extração de áudio SIMPLIFICADA e COMPATÍVEL
            # Primeiro tentativa: versão básica e compatível
            ffmpeg_cmd_basic = [
                "ffmpeg",
                "-y",  # sobrescreve arquivo existente
                "-i", str(video_path),
                "-vn",  # remove streams de vídeo
                "-ac", "1",  # mono (reduz tamanho em ~50%)
                "-ar", "16000",  # 16kHz (otimizado para fala humana)
                "-acodec", "pcm_s16le",  # codec WAV sem perda
                str(audio_wav),
            ]
            
            # Segunda tentativa: com filtros básicos se a primeira falhar
            ffmpeg_cmd_filtered = [
                "ffmpeg",
                "-y",
                "-i", str(video_path),
                "-vn",
                "-ac", "1",
                "-ar", "16000",
                "-acodec", "pcm_s16le",
                # Filtros básicos e universalmente compatíveis
                "-af", "silenceremove=start_periods=1:start_threshold=-50dB",
                str(audio_wav),
            ]
            
            logger.info("Extraindo áudio do MP4...")
            extraction_start = time.time()
            
            # Tentativa 1: Comando básico (mais compatível)
            try:
                logger.info("Tentando extração básica...")
                result = subprocess.run(
                    ffmpeg_cmd_basic, 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                logger.info("✅ Extração básica bem-sucedida")
                
            except subprocess.CalledProcessError as e:
                logger.warning(f"❌ Extração básica falhou: {e.stderr}")
                
                # Tentativa 2: Com filtro simples
                try:
                    logger.info("Tentando extração com filtro simples...")
                    result = subprocess.run(
                        ffmpeg_cmd_filtered,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info("✅ Extração com filtro bem-sucedida")
                    
                except subprocess.CalledProcessError as e2:
                    logger.error(f"❌ Todas as tentativas falharam")
                    logger.error(f"Erro básico: {e.stderr}")
                    logger.error(f"Erro com filtro: {e2.stderr}")
                    
                    # Tentativa 3: Comando minimalista (último recurso)
                    logger.info("Tentando comando minimalista...")
                    ffmpeg_cmd_minimal = [
                        "ffmpeg", "-y", "-i", str(video_path), 
                        "-vn", "-acodec", "pcm_s16le", str(audio_wav)
                    ]
                    
                    result = subprocess.run(
                        ffmpeg_cmd_minimal,
                        capture_output=True,
                        text=True,
                        check=True
                    )
                    logger.info("✅ Extração minimalista bem-sucedida")
            
            extraction_time = time.time() - extraction_start
            logger.info(f"Extração concluída em {extraction_time:.2f}s")
            
            # Verifica se o arquivo WAV foi criado
            if not audio_wav.exists() or audio_wav.stat().st_size == 0:
                raise RuntimeError("Falha na extração de áudio - arquivo WAV vazio ou não criado")

            # Calcula duração FINAL do áudio processado
            try:
                final_duration_cmd = [
                    "ffprobe",
                    "-v", "quiet",
                    "-show_entries", "format=duration",
                    "-of", "default=noprint_wrappers=1:nokey=1",
                    str(audio_wav)
                ]
                
                final_duration_result = subprocess.run(final_duration_cmd, capture_output=True, text=True, check=True)
                final_duration = float(final_duration_result.stdout.strip()) if final_duration_result.stdout.strip() else duration_seconds
                
                if final_duration != duration_seconds and duration_seconds > 0:
                    economy_percent = ((duration_seconds - final_duration) / duration_seconds) * 100
                    logger.info(f"Duração após processamento: {final_duration:.2f}s (original: {duration_seconds:.2f}s)")
                    logger.info(f"Economia: {economy_percent:.1f}%")
                else:
                    logger.info(f"Duração do áudio: {final_duration:.2f}s")
                    
            except Exception as e:
                logger.warning(f"Não foi possível calcular duração final: {e}")
                final_duration = duration_seconds

            # Transcrição OTIMIZADA com OpenAI Whisper
            logger.info("Iniciando transcrição otimizada com OpenAI Whisper...")
            transcription_start = time.time()
            
            with open(audio_wav, "rb") as f:
                result = client.audio.transcriptions.create(
                    model=MODEL,
                    file=f,
                    language=LANGUAGE,  # Especificar idioma melhora precisão
                    response_format="verbose_json",  # Para obter detalhes e segmentos
                    
                    # PARÂMETROS OTIMIZADOS para maior precisão:
                    temperature=0.0,  # Determinístico (mais assertivo, menos criativo)
                    
                    # Prompt inicial para melhorar contexto (português brasileiro)
                    prompt="Este é um áudio em português brasileiro. Transcreva com pontuação adequada e formatação correta."
                )
            
            transcription_time = time.time() - transcription_start
            
            # Extrai o texto e informações detalhadas da resposta
            transcription_text = result.text if hasattr(result, 'text') else str(result)
            
            # Calcula tokens baseado na duração OTIMIZADA (pós-processamento)
            # Usar a duração final (após remoção de silêncios) para cálculo mais preciso
            estimated_tokens = int((final_duration / 60) * 175)  # 175 tokens por minuto
            
            # Análise de qualidade da transcrição
            if not transcription_text.strip():
                logger.warning("Transcrição retornou texto vazio")
                transcription_text = "[Áudio sem conteúdo de fala detectado]"
                estimated_tokens = 0
            else:
                # Análise básica da qualidade
                word_count = len(transcription_text.split())
                chars_count = len(transcription_text)
                
                # Métricas de eficiência
                words_per_second = word_count / final_duration if final_duration > 0 else 0
                chars_per_token = chars_count / estimated_tokens if estimated_tokens > 0 else 0
                
                # Log de métricas de qualidade
                logger.info(f"Qualidade da transcrição:")
                logger.info(f"  - Palavras: {word_count}")
                logger.info(f"  - Caracteres: {chars_count}")
                logger.info(f"  - Palavras/segundo: {words_per_second:.1f}")
                logger.info(f"  - Caracteres/token: {chars_per_token:.1f}")
                
                # Validação de qualidade básica
                if words_per_second > 8:  # Muito rápido para fala humana normal
                    logger.warning("Taxa de palavras muito alta - possível erro na transcrição")
                elif words_per_second < 0.5 and final_duration > 10:  # Muito lento
                    logger.warning("Taxa de palavras muito baixa - áudio pode ter pouco conteúdo")
            
            # Cálculo de economia total
            original_cost_minutes = duration_seconds / 60
            optimized_cost_minutes = final_duration / 60
            cost_savings = original_cost_minutes - optimized_cost_minutes
            
            logger.info(f"Transcrição OTIMIZADA concluída:")
            logger.info(f"  - Tempo de processamento: {transcription_time:.2f}s")
            logger.info(f"  - Duração original: {duration_seconds:.2f}s")
            logger.info(f"  - Duração otimizada: {final_duration:.2f}s")
            logger.info(f"  - Economia de custo: {cost_savings * 60:.1f}s ({cost_savings:.2f} minutos)")
            logger.info(f"  - Tokens estimados: {estimated_tokens}")
            
            return TranscriptionResult(
                text=transcription_text,
                tokens_used=estimated_tokens,
                model_used=MODEL,
                duration_seconds=final_duration  # Usar duração otimizada
            )
            
    except subprocess.CalledProcessError as e:
        error_msg = f"Erro no FFmpeg: {e.stderr if e.stderr else str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    except Exception as e:
        error_msg = f"Erro inesperado na transcrição: {str(e)}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

def test_ffmpeg_installation():
    """
    Testa se FFmpeg está instalado e funcionando corretamente.
    
    Returns:
        dict: Informações sobre a instalação do FFmpeg
    """
    try:
        check_ffmpeg_installation()
        
        # Testa ffmpeg
        ffmpeg_result = subprocess.run(
            ["ffmpeg", "-version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Testa ffprobe
        ffprobe_result = subprocess.run(
            ["ffprobe", "-version"], 
            capture_output=True, 
            text=True, 
            check=True
        )
        
        # Extrai versões
        ffmpeg_version = ffmpeg_result.stdout.split('\n')[0] if ffmpeg_result.stdout else "Versão não identificada"
        ffprobe_version = ffprobe_result.stdout.split('\n')[0] if ffprobe_result.stdout else "Versão não identificada"
        
        return {
            "status": "success",
            "ffmpeg_installed": True,
            "ffprobe_installed": True,
            "ffmpeg_version": ffmpeg_version,
            "ffprobe_version": ffprobe_version
        }
        
    except RuntimeError as e:
        return {
            "status": "error",
            "ffmpeg_installed": False,
            "ffprobe_installed": False,
            "error": str(e)
        }
    except Exception as e:
        return {
            "status": "error",
            "ffmpeg_installed": False,
            "ffprobe_installed": False,
            "error": f"Erro inesperado: {str(e)}"
        }

# Função de teste opcional
if __name__ == "__main__":
    # Teste a instalação do FFmpeg
    test_result = test_ffmpeg_installation()
    print("Teste de instalação do FFmpeg:")
    print(f"Status: {test_result['status']}")
    if test_result['status'] == 'success':
        print(f"FFmpeg: {test_result['ffmpeg_version']}")
        print(f"FFProbe: {test_result['ffprobe_version']}")
    else:
        print(f"Erro: {test_result['error']}")
