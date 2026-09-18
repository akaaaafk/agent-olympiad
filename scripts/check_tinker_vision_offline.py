"""Render repaired puzzle pages through the real Tinker SDK without paid sampling."""
import argparse
import json
import os
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.output.exists():
        parser.error('Use a fresh output file')
    import tinker
    from transformers import AutoTokenizer
    from llm import LLMRequest,make_tinker_request_fn
    from problem_pdf import read_problem_pdf
    model='Qwen/Qwen3.6-35B-A3B'
    tokenizer=AutoTokenizer.from_pretrained(model)
    client=Mock();client.get_tokenizer.return_value=tokenizer
    client.sample.return_value.result.return_value=SimpleNamespace(sequences=[
        SimpleNamespace(tokens=tokenizer.encode('OK',add_special_tokens=False),stop_reason='stop')])
    service=Mock();service.create_sampling_client.return_value=client
    rows=json.loads((ROOT/'data/benchmarks/mystery_hunt/benchmark.json').read_text(encoding='utf-8'))
    cases=[]
    # Only replace remote sampling. Local tokenizer, processor, renderer and SDK
    # request serialization are real. No credentials or service requests needed.
    with patch.dict(os.environ,{'TINKER_API_KEY':'offline-fixture'}),patch.object(tinker,'ServiceClient',return_value=service):
        fn=make_tinker_request_fn(model,max_output_tokens=16)
        for pid,count in [('mystery_hunt_01261',8),('mystery_hunt_01271',1),('mystery_hunt_01277',1),('mystery_hunt_01278',2)]:
            row=next(r for r in rows if r['problem_id']==pid)
            for start in range(1,count+1,2):
                pages=list(range(start,min(count,start+1)+1))
                _,images=read_problem_pdf(row,pages=pages)
                response=fn(LLMRequest('Read the supplied task.',row['problem_description'],attachments=tuple(images)))
                prompt=client.sample.call_args.args[0]
                chunks=[c for c in prompt.chunks if c.type=='image']
                assert len(chunks)==len(pages)
                assert all(c.data and c.expected_tokens>0 for c in chunks)
                serialized=prompt.model_dump(mode='json')
                assert len([c for c in serialized['chunks'] if c['type']=='image'])==len(pages)
                assert response.usage['input_tokens']==prompt.length
                cases.append(dict(problem_id=pid,pages=pages,image_tokens=[c.expected_tokens for c in chunks],input_tokens=prompt.length,status='PASS'))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(dict(model=model,cases=cases,paid_calls=0,
        scope='Real local rendering and SDK image payload serialization; remote sampling mocked.'),indent=2),encoding='utf-8')
    print(json.dumps(dict(cases=len(cases),pages=sum(len(c['pages']) for c in cases),status='PASS',paid_calls=0)))


if __name__=='__main__':main()
