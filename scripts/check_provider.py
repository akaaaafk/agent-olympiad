"""Small authenticated provider preflight, without running any benchmark."""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))


def main(argv=None):
    from env_config import PROVIDERS, add_run_credentials, consume_run_credentials, load_repo_dotenv
    from llm import LLMRequest, LLMAttachment, resolve_request_fn, provider_capabilities
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--provider', choices=PROVIDERS, required=True)
    parser.add_argument('--model', required=True)
    parser.add_argument('--temperature', type=float, default=0.2)
    parser.add_argument('--pdf', type=Path, help='Optional PDF to check, sending only page 1')
    parser.add_argument('--pdf-expected-text', help='Optional literal marker expected in the PDF response')
    add_run_credentials(parser)
    args = parser.parse_args(argv)
    load_repo_dotenv()
    consume_run_credentials(args)
    if args.pdf_expected_text and not args.pdf:
        parser.error('--pdf-expected-text requires --pdf')
    call = resolve_request_fn(args.provider, args.model, max_output_tokens=1024, temperature=args.temperature)
    checks = []
    def check_response(response):
        if response.usage.get('tool_error'):
            raise ValueError(response.usage['tool_error'])
    text = call(LLMRequest('Follow the instruction exactly.', 'Reply with exactly OK.'))
    check_response(text)
    if text.text.strip() != 'OK':
        raise ValueError('Text check failed: model did not return OK')
    checks.append('authenticated_text')
    tools = ({'type': 'function', 'name': 'provider_probe', 'description': 'Return the probe value',
              'parameters': {'type': 'object', 'properties': {'value': {'type': 'integer'}},
                             'required': ['value'], 'additionalProperties': False}},)
    tool = call(LLMRequest('Use the provided tool.', 'Call provider_probe with value 7.',
                          tools=tools, tool_choice='required', parallel_tool_calls=False))
    check_response(tool)
    if (len(tool.tool_calls) != 1 or tool.tool_calls[0].name != 'provider_probe'
            or tool.tool_calls[0].arguments != {'value': 7}):
        raise ValueError('Tool check failed: expected exactly one provider_probe(value=7)')
    checks.append('native_tools' if provider_capabilities(args.provider).native_tools else 'emulated_tools')
    if args.pdf:
        pdf = call(LLMRequest('Read the supplied PDF page.', 'Quote the first heading on this page.',
            attachments=(LLMAttachment(args.pdf.resolve(), 'application/pdf', 'agent_visible', 1, 1),)))
        check_response(pdf)
        if not pdf.text.strip():
            raise ValueError('PDF transport check returned no text')
        if args.pdf_expected_text and args.pdf_expected_text not in pdf.text:
            raise ValueError('PDF content check failed: expected text not found')
        checks.append('pdf_content' if args.pdf_expected_text else 'pdf_transport_only')
    print(json.dumps({'provider': args.provider, 'model': args.model, 'passed': checks,
                      'pdf_mode': 'text' if provider_capabilities(args.provider).pdf_text else 'native'}, indent=2))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        # SDK messages can contain request details. Do not print them or keys.
        print(f'Provider check failed ({type(exc).__name__}). Check endpoint, credentials, '
              'model permissions and requested capabilities.', file=sys.stderr)
        raise SystemExit(1)
