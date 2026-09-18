"""Local images/PDF pages to the official Tinker Qwen multimodal renderer."""
import io
from llm_usage import local_preflight


def renderer_name(model):
    name = model.split(':', 1)[0].lower()
    if name.startswith(('qwen/qwen3.5-', 'qwen/qwen3.6-')):
        return 'qwen3_5_disable_thinking'
    return None


@local_preflight
def request_images(request):
    """Honor explicit PDF page bounds; never fall back to text or drop an image."""
    from PIL import Image
    import pymupdf
    images = []
    for asset in request.attachments:
        if request.purpose not in {'evaluation', 'grading', 'judge'} and asset.role != 'agent_visible':
            raise ValueError('Judge-only attachments cannot be sent to contestants.')
        if asset.mime_type == 'application/pdf':
            with pymupdf.open(asset.path) as doc:
                start = asset.page_start if asset.page_start is not None else 1
                end = asset.page_end if asset.page_end is not None else len(doc)
                if (asset.page_start is None) != (asset.page_end is None) or not 1 <= start <= end <= len(doc):
                    raise ValueError('Invalid PDF page range for Tinker vision')
                for i in range(start-1, end):
                    pix = doc[i].get_pixmap(dpi=144, colorspace=pymupdf.csRGB, alpha=False)
                    images.append(Image.open(io.BytesIO(pix.tobytes('png'))).convert('RGB'))
        elif asset.mime_type.startswith('image/'):
            with Image.open(asset.path) as image:
                if getattr(image, 'n_frames', 1) != 1:
                    raise ValueError('Animated images require explicit frame selection')
                # Preserve transparent artwork against a white document background.
                rgba = image.convert('RGBA')
                background = Image.new('RGBA', rgba.size, 'white')
                background.alpha_composite(rgba)
                images.append(background.convert('RGB'))
        else:
            raise ValueError(f'Unsupported Tinker attachment MIME type: {asset.mime_type}')
    return tuple(images)


def make_renderer(model, tokenizer):
    name = renderer_name(model)
    if name is None:
        raise ValueError(f'Tinker vision renderer not configured for {model}')
    from tinker_cookbook import renderers
    from tinker_cookbook.image_processing_utils import get_image_processor
    return renderers.get_renderer(name, tokenizer, image_processor=get_image_processor(model))


def generation_input(renderer, tokenizer, system, user, images, prefix='', continuation=None):
    import tinker
    content = [{'type': 'text', 'text': user}]
    for i, image in enumerate(images, 1):
        content.extend([{'type': 'text', 'text': f'\nAttachment image {i}:\n'},
                        {'type': 'image', 'image': image}])
    # Harmony owns a built-in system message carrying reasoning effort; its
    # official helper places application instructions in the developer role.
    instructions = (renderer.create_conversation_prefix_with_tools([], system)
                    if getattr(renderer, 'use_system_prompt', False) is True
                    else [{'role': 'system', 'content': system}])
    prompt = renderer.build_generation_prompt([*instructions, {'role': 'user', 'content': content}])
    suffix = list(tokenizer.encode(prefix, add_special_tokens=False)) if prefix else []
    suffix += list(continuation or [])
    if suffix:
        prompt = tinker.ModelInput(chunks=[*prompt.chunks, tinker.EncodedTextChunk(tokens=suffix)])
    return prompt
