"""
clipboard_utils.py
==================
Copia texto para o clipboard do Windows.

Estratégia para Telegram Desktop
---------------------------------
Telegram Desktop ignora CF_HTML ao colar — lê apenas texto puro (CF_UNICODETEXT).
Por isso, a abordagem correta é copiar texto com marcadores **Telegram Markdown v1**:
    **texto** → negrito na mensagem enviada
    _texto_   → itálico na mensagem enviada

Ao colar no Telegram Desktop e ENVIAR, os markers `**` somem e o negrito aparece.

Funções disponíveis
-------------------
copy_text_to_clipboard(text)  — copia texto puro via clip.exe (mais simples)
copy_html_to_clipboard(html)  — copia CF_HTML+texto via Win32 ctypes (apps que leem HTML)

Dependências: nenhuma além da stdlib.
"""

import ctypes
import os
import platform
import re
import subprocess
import tempfile

# ---------------------------------------------------------------------------
# Detecção de ambiente
# ---------------------------------------------------------------------------

def _is_windows() -> bool:
    return platform.system() == "Windows"


# ---------------------------------------------------------------------------
# Cópia de texto puro — principal para Telegram
# ---------------------------------------------------------------------------

def copy_text_to_clipboard(text: str) -> tuple:
    """
    Copia texto puro para o clipboard.

    - Windows local: usa clip.exe (nativo) com fallback para ctypes Win32.
    - Linux / Streamlit Cloud: retorna (False, "server") — o chamador deve
      renderizar o botão JavaScript via render_web_copy_button().

    Retorna (True, "") em sucesso ou (False, código_de_erro).
    """
    if not _is_windows():
        return False, "server"

    try:
        # Python's encode('utf-16') inclui BOM automaticamente — clip.exe precisa disso
        encoded = text.encode("utf-16")
        result  = subprocess.run(
            "clip",
            input=encoded,
            capture_output=True,
            timeout=5,
        )
        if result.returncode != 0:
            return _copy_text_ctypes(text)
        return True, ""
    except FileNotFoundError:
        return _copy_text_ctypes(text)
    except subprocess.TimeoutExpired:
        return False, "clip.exe demorou demais (timeout 5s)."
    except Exception as exc:
        return False, str(exc)


# ---------------------------------------------------------------------------
# Botão JavaScript para ambiente web (Streamlit Cloud)
# ---------------------------------------------------------------------------

def render_web_copy_button(text: str, label: str = "📋 Copiar para Telegram") -> None:
    """
    Renderiza um botão HTML/JS que copia `text` para o clipboard do BROWSER.

    Funciona em qualquer ambiente web com HTTPS (ex: Streamlit Cloud).
    Usa navigator.clipboard.writeText() — API nativa dos browsers modernos.
    O texto é serializado via json.dumps() para escapar com segurança todos
    os caracteres especiais (aspas, barras, emojis, quebras de linha etc.).
    """
    import json
    import streamlit.components.v1 as components

    text_json = json.dumps(text)   # escaping seguro para JS

    html = f"""
<button
  id="webCopyBtn"
  onclick="
    navigator.clipboard.writeText({text_json})
      .then(function() {{
        document.getElementById('webCopyBtn').textContent = '✅ Copiado! Cole no Telegram.';
        document.getElementById('webCopyBtn').style.background = '#155724';
      }})
      .catch(function(e) {{
        document.getElementById('webCopyBtn').textContent = '❌ Erro: ' + e;
      }});
  "
  style="
    background:#1d6f42; color:white; border:none;
    padding:8px 18px; border-radius:6px; cursor:pointer;
    font-size:14px; font-weight:bold; margin:4px 0;
  "
>{label}</button>
"""
    components.html(html, height=50)


def _copy_text_ctypes(text: str) -> tuple:
    """Fallback: copia texto via Win32 API ctypes (sem clip.exe)."""
    try:
        user32   = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        kernel32.GlobalAlloc.argtypes  = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype   = ctypes.c_void_p
        kernel32.GlobalLock.argtypes   = [ctypes.c_void_p]
        kernel32.GlobalLock.restype    = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalUnlock.restype  = ctypes.c_bool
        user32.OpenClipboard.argtypes   = [ctypes.c_void_p]
        user32.OpenClipboard.restype    = ctypes.c_bool
        user32.EmptyClipboard.restype   = ctypes.c_bool
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype  = ctypes.c_void_p
        user32.CloseClipboard.restype    = ctypes.c_bool

        CF_UNICODETEXT = 13
        GMEM_MOVEABLE  = 0x0002

        plain_bytes = text.encode("utf-16-le") + b"\x00\x00"
        hMem = kernel32.GlobalAlloc(GMEM_MOVEABLE, ctypes.c_size_t(len(plain_bytes)))
        if not hMem:
            return False, "GlobalAlloc falhou."
        pMem = kernel32.GlobalLock(hMem)
        if not pMem:
            return False, "GlobalLock falhou."
        ctypes.memmove(pMem, plain_bytes, len(plain_bytes))
        kernel32.GlobalUnlock(hMem)

        user32.OpenClipboard(0)
        user32.EmptyClipboard()
        user32.SetClipboardData(CF_UNICODETEXT, hMem)
        user32.CloseClipboard()
        return True, ""
    except Exception as exc:
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
        return False, str(exc)


# ---------------------------------------------------------------------------
# Helpers (mantidos para compatibilidade com copy_html_to_clipboard)
# ---------------------------------------------------------------------------

def strip_html_tags(html: str) -> str:
    """Remove tags HTML para gerar texto puro de fallback."""
    text = re.sub(r"<br\s*/?>", "\n", html, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    return text


def build_cf_html(html_fragment: str) -> str:
    """
    Constrói o payload no formato CF_HTML (Windows HTML Clipboard Format).

    Referência oficial:
    https://docs.microsoft.com/en-us/windows/win32/dataxchg/html-clipboard-format

    O formato exige um cabeçalho de texto com offsets de byte, seguido do
    documento HTML completo com marcadores <!--StartFragment--> e <!--EndFragment-->.
    """
    HEADER_TEMPLATE = (
        "Version:0.9\r\n"
        "StartHTML:{StartHTML:08d}\r\n"
        "EndHTML:{EndHTML:08d}\r\n"
        "StartFragment:{StartFragment:08d}\r\n"
        "EndFragment:{EndFragment:08d}\r\n"
    )

    pre  = "<!DOCTYPE html>\r\n<html>\r\n<body>\r\n<!--StartFragment-->"
    post = "<!--EndFragment-->\r\n</body>\r\n</html>"

    # Calcula tamanho do header usando placeholders (todos zeros)
    placeholder = HEADER_TEMPLATE.format(
        StartHTML=0, EndHTML=0, StartFragment=0, EndFragment=0
    )
    header_len = len(placeholder.encode("utf-8"))

    start_html = header_len
    start_frag = header_len + len(pre.encode("utf-8"))
    end_frag   = start_frag + len(html_fragment.encode("utf-8"))
    end_html   = end_frag   + len(post.encode("utf-8"))

    header = HEADER_TEMPLATE.format(
        StartHTML=start_html,
        EndHTML=end_html,
        StartFragment=start_frag,
        EndFragment=end_frag,
    )
    return header + pre + html_fragment + post


# ---------------------------------------------------------------------------
# Função principal
# ---------------------------------------------------------------------------

def copy_html_to_clipboard(html_fragment: str, plain_text: str = None) -> tuple:
    """
    Copia HTML para o clipboard do Windows via Win32 API (ctypes).

    Usa a API nativa do Windows diretamente — sem subprocesso, sem dependências extras.
    Funciona no contexto do Streamlit local porque o processo Python já tem acesso
    ao clipboard da sessão do usuário (mesmo window station).

    Formatos gravados no clipboard:
      CF_HTML (49)    → "HTML Format" — Telegram Desktop lê e renderiza negrito/itálico
      CF_UNICODETEXT  → texto puro — fallback para apps que não leem CF_HTML

    Parâmetros
    ----------
    html_fragment : str
        HTML com <b>, <i>, <br> (fragmento sem <html>/<body>). Emojis suportados.

    plain_text : str | None
        Fallback texto puro. Se None, gera automaticamente removendo as tags.

    Retorna
    -------
    (success: bool, error_msg: str)
    """
    if plain_text is None:
        plain_text = strip_html_tags(html_fragment)

    try:
        user32   = ctypes.windll.user32
        kernel32 = ctypes.windll.kernel32

        # Declara argtypes + restype corretos para pointers em 64 bits
        kernel32.GlobalAlloc.argtypes  = [ctypes.c_uint, ctypes.c_size_t]
        kernel32.GlobalAlloc.restype   = ctypes.c_void_p
        kernel32.GlobalLock.argtypes   = [ctypes.c_void_p]
        kernel32.GlobalLock.restype    = ctypes.c_void_p
        kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]
        kernel32.GlobalUnlock.restype  = ctypes.c_bool
        user32.RegisterClipboardFormatW.argtypes = [ctypes.c_wchar_p]
        user32.RegisterClipboardFormatW.restype  = ctypes.c_uint
        user32.OpenClipboard.argtypes   = [ctypes.c_void_p]
        user32.OpenClipboard.restype    = ctypes.c_bool
        user32.EmptyClipboard.restype   = ctypes.c_bool
        user32.SetClipboardData.argtypes = [ctypes.c_uint, ctypes.c_void_p]
        user32.SetClipboardData.restype  = ctypes.c_void_p
        user32.CloseClipboard.restype    = ctypes.c_bool

        # Registra o formato CF_HTML
        CF_HTML = user32.RegisterClipboardFormatW("HTML Format")
        if CF_HTML == 0:
            return False, "Não foi possível registrar o formato HTML Format no clipboard."

        CF_UNICODETEXT = 13  # constante do Windows
        GMEM_MOVEABLE  = 0x0002

        def _alloc_global(data_bytes: bytes) -> ctypes.c_void_p:
            """Aloca memória global e copia bytes — retorna o handle hMem."""
            size = len(data_bytes)
            hMem = kernel32.GlobalAlloc(GMEM_MOVEABLE, ctypes.c_size_t(size))
            if not hMem:
                raise MemoryError("GlobalAlloc falhou")
            pMem = kernel32.GlobalLock(hMem)
            if not pMem:
                raise MemoryError(f"GlobalLock falhou (hMem={hMem})")
            ctypes.memmove(pMem, data_bytes, size)
            kernel32.GlobalUnlock(hMem)
            return hMem

        # --- Abre o clipboard ---
        if not user32.OpenClipboard(0):
            return False, "OpenClipboard falhou — outro processo pode ter o clipboard aberto."
        try:
            user32.EmptyClipboard()

            # CF_HTML: CF_HTML usa UTF-8 + null terminator (1 byte)
            cf_html_str   = build_cf_html(html_fragment)
            cf_html_bytes = cf_html_str.encode("utf-8") + b"\x00"
            hHtml = _alloc_global(cf_html_bytes)
            user32.SetClipboardData(CF_HTML, hHtml)

            # CF_UNICODETEXT: UTF-16-LE + null terminator wide (2 bytes já inclusos)
            plain_bytes = plain_text.encode("utf-16-le") + b"\x00\x00"
            hText = _alloc_global(plain_bytes)
            user32.SetClipboardData(CF_UNICODETEXT, hText)

        finally:
            user32.CloseClipboard()

        return True, ""

    except Exception as exc:
        # Garante que o clipboard seja fechado em caso de erro inesperado
        try:
            ctypes.windll.user32.CloseClipboard()
        except Exception:
            pass
        return False, str(exc)
