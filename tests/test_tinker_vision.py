"""Image transport through real SDK types, with network sampling replaced."""
import io
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import pytest
from PIL import Image
import pymupdf
import tinker
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
import llm
import tinker_vision as vision
from test_tinker_action_mechanism import Samples, request
from dataclasses import replace
MODEL='Qwen/Qwen3.6-35B-A3B'


@pytest.fixture
def asset(tmp_path):
    p=tmp_path/'image.png'; Image.new('RGB',(112,112),'red').save(p)
    return llm.LLMAttachment(p,'image/png')


def test_page_bounds_order_and_role_isolation(tmp_path):
    p=tmp_path/'pages.pdf'
    with pymupdf.open() as doc:
        for color in [(1,0,0),(0,1,0),(0,0,1)]:
            page=doc.new_page(width=72,height=72);page.draw_rect(page.rect,color=color,fill=color)
        doc.save(p)
    a=llm.LLMAttachment(p,'application/pdf',page_start=2,page_end=3)
    images=vision.request_images(llm.LLMRequest('','',attachments=(a,)))
    assert len(images)==2
    assert images[0].getpixel((50,50))==(0,255,0)
    assert images[1].getpixel((50,50))==(0,0,255)
    for start,end in [(0,2),(3,2),(1,4),(None,2),(1,None)]:
        with pytest.raises(ValueError,match='page range'):
            vision.request_images(llm.LLMRequest('','',attachments=(replace(a,page_start=start,page_end=end),)))
    with pytest.raises(ValueError,match='Judge-only'):
        llm.LLMRequest('','',attachments=(replace(a,role='judge_only'),))
    assert len(vision.request_images(llm.LLMRequest('','',purpose='evaluation',attachments=(replace(a,role='judge_only'),))))==2


def test_every_action_stage_and_continuation_keeps_images(asset):
    sampler=Samples(('submit_code"',2,'stop'),('q"',2,'stop'),('first',5,'length'),(' second',5,'stop'))
    sampler.supports_prefix=True
    with patch.object(llm,'make_tinker_caller',return_value=sampler):
        fn=llm.make_tinker_request_fn(MODEL)
    response=fn(replace(request(),attachments=(asset,)))
    assert response.tool_calls[0].arguments['code']=='first second'
    assert len(sampler.requests)==4
    for _,_,kwargs in sampler.requests:
        assert kwargs['images'][0].getpixel((0,0))==(255,0,0)
    assert sampler.requests[-1][2]['continuation_tokens']==list(map(ord,'first'))
    assert fn.supports_attachments and not fn.supports_pdf_text


def test_native_sdk_receives_image_chunks_and_counts_image_context(asset):
    tokenizer=Mock();tokenizer.encode.side_effect=lambda s,**kw:list(map(ord,s));tokenizer.decode.return_value='OK'
    client=Mock();client.get_tokenizer.return_value=tokenizer
    client.sample.return_value.result.return_value=SimpleNamespace(sequences=[SimpleNamespace(tokens=[1,2],stop_reason='stop')])
    service=Mock();service.create_sampling_client.return_value=client
    image_bytes=asset.path.read_bytes()
    renderer=Mock()
    renderer.get_stop_sequences.return_value=['<|im_end|>']
    renderer.build_generation_prompt.return_value=tinker.ModelInput(chunks=[
        tinker.EncodedTextChunk(tokens=[42]),tinker.types.ImageChunk(data=image_bytes,format='png',expected_tokens=64)])
    with patch.dict(os.environ,{'TINKER_API_KEY':'offline-fixture'}), patch.object(tinker,'ServiceClient',return_value=service), patch.object(vision,'make_renderer',return_value=renderer):
        call=llm.make_tinker_caller(MODEL)
        assert call('sys','user',images=vision.request_images(llm.LLMRequest('','',attachments=(asset,))),assistant_prefix='P',continuation_tokens=[99])=='OK'
        sent=client.sample.call_args.args[0]
        assert sent.chunks[1].data==image_bytes
        assert sent.chunks[-1].tokens==[ord('P'),99]
        assert call.last_usage['input_tokens']==67
        client.sample.reset_mock()
        renderer.build_generation_prompt.return_value=tinker.ModelInput(chunks=[tinker.types.ImageChunk(data=image_bytes,format='png',expected_tokens=65500)])
        with pytest.raises(RuntimeError,match='context window'):
            call('sys','user',images=(Image.new('RGB',(112,112)),))
        client.sample.assert_not_called()


def test_generation_passes_images_and_text_models_refuse_them(asset):
    sampler=Mock(return_value='done')
    with patch.object(llm,'make_tinker_caller',return_value=sampler):
        fn=llm.make_tinker_request_fn(MODEL)
        assert fn(llm.LLMRequest('sys','user',attachments=(asset,))).text=='done'
        assert sampler.call_args.kwargs['images'][0].size==(112,112)
        text_fn=llm.make_tinker_request_fn('text-model')
        with pytest.raises(ValueError,match='PDFs only'):
            text_fn(llm.LLMRequest('','',attachments=(asset,)))
    assert llm.provider_capabilities('tml',MODEL).attachments
    assert llm.provider_capabilities('tinker','text-model').pdf_text


def test_artifact_loop_uses_visual_delivery_for_current_model(tmp_path):
    import json
    from otc_artifact_pipeline import prepare_artifact_run,run_artifact_contest
    from evaluation.models import load_rubric
    p=tmp_path/'task.pdf'
    with pymupdf.open() as doc:
        for color in [(1,0,0),(0,0,1)]:
            page=doc.new_page(width=72,height=72);page.draw_rect(page.rect,color=color,fill=color)
        doc.save(p)
    prepared=prepare_artifact_run(competition='vis_moot',task_pdf=p,task_pages='1-1',
        output=tmp_path/'run',max_turns=2,provider='tinker',model=MODEL,
        judge_model=MODEL,system_variant='single_agent')
    rubric=load_rubric(prepared['rubric'])
    payload=dict(criteria=[dict(id=c.id,score=c.min_score,max_score=c.max_score,
        evidence=['Offline fixture'],justification='Protocol check',confidence=1,observable=c.observable)
        for c in rubric.criteria],total_score=sum(c.min_score for c in rubric.criteria),
        max_score=rubric.total_points,warnings=[],limitations=[])
    calls=[]
    def sampler(system,user,**kwargs):
        images=kwargs['images']; calls.append(len(images))
        assert images[0].getpixel((50,50))==(255,0,0)
        if 'expert olympiad grader' in system:return json.dumps(payload)
        tools=json.JSONDecoder().raw_decode(system.split('FUNCTION SCHEMAS:\n')[1])[0]
        names={t['name'] for t in tools}
        if 'render_pdf' in names:return json.dumps(dict(name='render_pdf',arguments={'content':'Offline fixture report'}))
        return json.dumps(dict(name='select_problem',arguments={'problem_id':'deliverable'}))
    with patch.object(llm,'make_tinker_caller',return_value=sampler):
        agent=llm.make_tinker_request_fn(MODEL);judge=llm.make_tinker_request_fn(MODEL)
    result=run_artifact_contest(prepared,agent_request=agent,judge_request=judge)
    assert result['status']=='complete' and result['graded']
    assert calls and not (tmp_path/'run/task_extracted.txt').exists()

