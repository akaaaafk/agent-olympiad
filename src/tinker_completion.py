"""Bounded exact-token recovery for non-tool completions and judges."""
from llm import LLMResponse


def complete(caller, request, model, limit, retries, images=()):
    def budget(name, default):
        value = request.metadata.get(name)
        if value is None:
            return default  # Unlimited contest budget still has bounded recovery.
        if type(value) is not int or value < 0:
            raise ValueError(f'{name} must be a nonnegative integer or None')
        return value
    attempts=min(1+retries, budget('max_transport_attempts',1+retries))
    remaining=budget('max_transport_output_tokens',limit*attempts)
    limit=min(limit,budget('max_output_tokens_override',limit))
    tokens=[]; trace=[]; text=''; error=None
    native=getattr(caller,'supports_sampling_metadata',False) is True
    can_continue=getattr(caller,'supports_continuation',False) is True
    usage={'api_calls':0,'input_tokens':0,'output_tokens':0,'unknown_usage_attempts':0,'max_output_tokens':limit,
           'tool_retries':0,'action_transport':'prompt_json','pdf_delivery':request.metadata.get('pdf_delivery'),
           'deduplicated_packet_pages':request.metadata.get('deduplicated_packet_pages',[])}
    for _ in range(max(0,attempts)):
        cap=min(limit,remaining)
        if cap<=0:break
        kwargs={'images':images} if images else {}
        if native:
            kwargs.update(max_retries=1,max_output_tokens_override=cap)
            if tokens:kwargs.update(continuation_tokens=list(tokens),preserve_whitespace=True)
            caller.last_usage={}
        try:
            raw=caller(request.system_prompt,request.user_prompt,**kwargs)
        except RuntimeError as exc:
            if not trace and not getattr(caller,'last_usage',{}):raise
            failed=getattr(caller,'last_usage',{}) if native else {}
            if not trace and failed.get('api_calls') == 0:
                exc.usage = dict(failed)
                raise
            failed = failed or {'api_calls': 1, 'unknown_usage_attempts': 1}
            trace.append(dict(failed))
            for key in ('api_calls','input_tokens','output_tokens','unknown_usage_attempts'):
                usage[key]+=failed.get(key,0)
            usage['transport_failed'] = True
            error=str(exc);break
        sample=dict(caller.last_usage) if native else dict(api_calls=1,output_tokens=max(1,len(raw)//4),finish_reason='stop')
        trace.append(sample)
        for key in ('api_calls','input_tokens','output_tokens','unknown_usage_attempts'):usage[key]+=sample.get(key,0)
        remaining-=sample.get('output_tokens',0)
        if can_continue:
            tokens.extend(caller.last_sample_tokens)
            text=caller.decode_completion_tokens(tokens)
        else:text=raw
        finish=sample.get('finish_reason','stop')
        usage['finish_reason']=finish
        usage['max_output_tokens']=sample.get('max_output_tokens',cap)
        if 'chat_template' in sample:usage['chat_template']=sample['chat_template']
        if 'chat_template_model' in sample:usage['chat_template_model']=sample['chat_template_model']
        if sample.get('output_tokens',0)>sample.get('max_output_tokens',cap):
            error='sample exceeded output budget';break
        if finish not in {'stop','length'}:
            error=f'incomplete or rejected completion ({finish})';break
        if finish=='stop':
            if not text.strip():
                error='completion has no visible final answer';break
            usage.update(continuation_samples=len(trace)-1,sampling_trace=trace)
            return LLMResponse(text.strip(),'tinker',model,usage=usage)
        if not can_continue:
            error='model adapter cannot resume exact tokens';break
    usage.update(tool_error=error or 'completion truncated; sampling budget exhausted',
                 finish_reason=usage.get('finish_reason','length'),incomplete_text=text,
                 continuation_samples=max(0,len(trace)-1),sampling_trace=trace)
    # Do not expose a truncated judge answer or a partial final answer as success.
    return LLMResponse('','tinker',model,usage=usage)
