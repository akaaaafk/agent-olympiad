"""Bind reviewed archival performance synopses to written-only scoring."""
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
from dataset_catalog import scorecard, update_track_index
from enable_remaining_mini_judges import criterion

TRACK = 'odyssey_of_the_mind'
# Archive list positions are not official problem numbers. Select by title.
CASES = {
    2010: ('Food Court', [
        'An accused food item defends itself against an accusation of being unhealthy.',
        'All characters are food items, including the accused, accuser and additional original characters.',
        'A jury not portrayed by team members reaches and reveals a decision to the audience.',
        'Explain a feasible staging design for the jury and respect the published $125 cost limit in an estimated materials plan.',
        'Provide an original humorous, coherent courtroom script with a clear resolution.']),
    2011: ('Full Circle', [
        'Something changes form or appearance at least three times and then returns to its original form and appearance in a final change.',
        'The script signals the audience each time a change occurs.',
        'Include a very silly character and a very serious character with distinct written characterization.',
        'Integrate a song and dance with specific cues and a plausible staging plan within the published $125 cost limit.',
        'Deliver an original humorous script with a surprise ending that coherently completes the cycle.']),
    2012: ('Odyssey Angels', [
        'Students travel through one or more original places and turn negative situations into positive ones.',
        'The students help two individuals with different problems through distinct plot events.',
        'They save an entire community from a bad situation through a coherent resolution.',
        'One Angel cannot speak and another has an original special power; realize both in the script and staging plan.',
        'Provide an original coherent script and a plausible estimated staging plan within the published $125 cost limit.']),
    2013: ('It\u2019s How You Look at It', [
        'Two characters behave naturally to themselves but unusually to people around them.',
        'Establish one character in a normal setting before showing others reacting to that character out of place.',
        'The other character starts by standing out and ends in a setting where its behavior is normal.',
        'Design a readable odd/normal meter and a creative scene change; explain how each supports the plot.',
        'Provide an original humorous coherent script and estimated staging costs within the published $125 limit.']),
    2014: ('Seeing is Believing', [
        'A community fears something in a location it has never visited, and the plot explores that fear.',
        'Townspeople use a creative method to choose one or more Travelers who visit and explore that location.',
        'A Traveler sends a message home using a specified means of communication to demonstrate there is nothing to fear.',
        'Integrate a narrator, two rhymes about the travels and a designed moving set piece.',
        'Provide an original coherent script and a feasible estimated staging plan within the published $125 cost limit.']),
    2015: ('Silent Movie', [
        'A Director produces and presents a silent movie with a clear beginning and end.',
        'A humorous villain performs three distinct silly acts of villainy.',
        'Movie characters do not speak during the movie; communicate their story through action and subtitles instead.',
        'Specify music on a team-created instrument, creatively displayed subtitles, and movie start/end signals.',
        'Provide an original coherent comic script and feasible estimated staging costs within the published $125 limit.']),
    2016: ('Furs, Fins, Feathers and Friends', [
        'Three different animals solve problems from their own distinct perspectives.',
        'The animals help a stranger and help one another through identifiable plot events.',
        'They solve a problem threatening the survival of all animals.',
        'Integrate singing, dancing and visible expressions of curiosity, sympathy, frustration and joy into the written plan.',
        'Provide an original humorous coherent script and estimated staging costs within the published $125 limit.']),
    2017: ('To Be Continued: A Superhero Cliffhanger', [
        'An unexpected superhero encounters three distinct situations requiring creativity to be saved.',
        'The hero changes appearance when using superpowers and blends back into society when not using them.',
        'Include a clumsy sidekick and a nemesis with clear roles in the plot.',
        'Write a choreographed battle and a cliffhanger ending; describe safe, plausible staging without claiming a performance.',
        'Provide an original humorous coherent script and estimated staging costs within the published $125 limit.']),
    2018: ('A Stellar Hangout', [
        'Set the action in an intergalactic hangout where creatures from different worlds stop, eat, refuel and relax.',
        'Create original creatures and foods with specific roles in the script.',
        'Integrate a search for space treasure into the hangout plot.',
        'Include a worker character, entertainment and a futuristic map with explicit staging descriptions.',
        'Provide an original humorous science-fiction script with coherent dialogue, scene transitions and a plausible design.']),
    2020: ('Gibberish or Not', [
        'Show gibberish being repeatedly misinterpreted as wisdom with concrete examples in the dialogue.',
        'A Champion arranges meetings with people in power and promotes the supposed ideas.',
        'Show the crowd accepting the supposed wisdom and a Child recognizing the misunderstanding.',
        'Integrate music and a wild celebration through specific written cues and a plausible staging design.',
        'Explain why the Child does not reveal the truth; provide a coherent creative resolution to the misunderstanding.']),
    2021: ('Superhero Socks: A Cliffhanger Beginning', [
        'Begin in a cliffhanger with a Superhero in peril and in need of escape.',
        'Super Socks grant a specified special power that the hero uses to escape.',
        'The hero fends off the adversary responsible for the initial predicament.',
        'Create an extreme-weather setting and a humorous character with clear written realization.',
        'Specify a sound cue every time Super Socks are activated and integrate it into a coherent original script and staging plan.']),
    2022: ('Life is a Circus!', [
        'A young person with a regular life wakes to find they have been transported to a circus world.',
        'Original animals perform unexpected tricks described as staged designs rather than actual animal performance.',
        'Include a clown, circus acts and a ringmaster announcing the activities.',
        'The person returns home thinking it was a dream, until a mysterious figure proves to be from the circus.',
        'Provide an original coherent script with distinct worlds, scene transitions and plausible staging cues.']),
    2023: ('The Most Dramatic Problem Ever!!!', [
        'A dramatic character overreacts to ordinary events in identifiable humorous scenes.',
        'Use different theatrical styles for the overreactions, evident in dialogue and stage directions.',
        'Include a situation where the reaction is justified but the character is ignored.',
        'Design something that grows and a costume representing two characters, with clear cues and plausible mechanisms.',
        'Provide an original humorous coherent script integrating the contrasts and design elements.']),
    2024: ('The Night Life', [
        'An explorer searches for things in nature that become active at night.',
        'Create an original discovery and show how the explorer encounters it.',
        'Include something that lights up, with an explicit proposed effect and activation cues.',
        'Represent a nocturnal animal through a team member in a described costume.',
        'Provide an original coherent script and plausible staging that integrates the nighttime setting and required elements.']),
    2025: ('AstronOMical Odyssey!', [
        'Set a humorous performance in an original fictional historical civilization.',
        'Present constellations and original stories explaining each, with a clear link between stories and star patterns.',
        'Include a humorous astronomer character with a specifically described stellar costume.',
        'Design a lighting effect and a shooting star with written cues and plausible mechanisms.',
        'Provide an original coherent script integrating the civilization, stories and effects without presenting invented history as fact.']),
    2026: ('Taller Tales of John Jivery', [
        'Create an original humorous tall tale with a clearly characterized hero or heroine.',
        'The hero or heroine performs an incredible feat realized in the written action.',
        'Include a unique fictional explanation of how something began or came to be.',
        'Include an audience surprise that follows coherently from the tale.',
        'Accompany each event with a visual weather effect representing an emotion; specify the cues and plausible stage design.']),
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def select_synopsis(text, title):
    body = text.split('---', 1)[1].strip()
    blocks = re.split(r'(?m)^\d+\.\s+', body)
    matches = [block.strip() for block in blocks if block.strip().startswith(title)]
    if len(matches) != 1:
        raise ValueError('Expected exactly one synopsis: ' + title)
    return matches[0]


def make_rubric(year, source, digest):
    title, requirements = CASES[year]
    return dict(rubric_id=f'odyssey_{year}_written_synopsis_v1', title=title + ' written benchmark',
        total_points=100,
        criteria=[criterion(f'requirement_{i}', f'Written requirement {i}', 20, text)
                  for i, text in enumerate(requirements, 1)],
        not_observable_from_deck=[
            'Public synopsis only; private full-problem constraints are not asserted or scored.',
            'Five equal 20-point benchmark criteria are not official historical scoring weights.',
            'Written script/design only; no live performance, construction, spontaneous score or cohort normalization.'],
        provenance=dict(sources=[dict(path=source, sha256=digest, selected_title=title)],
            weight_basis='Five equal benchmark weights operationalize this selected public synopsis.',
            official_score_equivalent=False))


def main():
    data = ROOT / 'data'
    path = data / f'benchmarks/{TRACK}/benchmark.json'
    rows = read(path)
    staged, originals, promoted = {}, {}, []
    backup = ROOT / 'tmp' / ('before_main_odyssey_expansion_' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'))
    def put(path, value):
        originals.setdefault(path, path.read_bytes() if path.exists() else None)
        staged[path] = (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8')

    rubrics = {}
    for row in rows:
        if row['year'] not in CASES or not row['problem_id'].endswith('_synopses'):
            continue
        if row['evaluation']['status'] != 'not_ready':
            continue
        assert len(row['assets']) == 1 and row['assets'][0]['role'] == 'agent_visible'
        asset = row['assets'][0]
        raw = (ROOT / asset['path']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == asset['sha256']
        title, requirements = CASES[row['year']]
        synopsis = select_synopsis(raw.decode('utf-8'), title)
        rubric = make_rubric(row['year'], asset['path'], asset['sha256'])
        rp = data / 'rubrics' / (rubric['rubric_id'] + '.json')
        put(rp, rubric)
        rubrics[row['problem_id']] = (rp, rubric)
        ev = row['evaluation']
        ev['before_main_synopsis_review'] = deepcopy(ev)
        ev.update(evaluator_id='rubric_llm_v1', status='ready_with_limitations',
            rubric_path=rp.relative_to(ROOT).as_posix(), reference_policy='rubric_only',
            grading_scope='written_artifact_benchmark', official_score_equivalent=False,
            deliverable='written_script_and_staging_plan', limitations=rubric['not_observable_from_deck'],
            score_basis=rubric['provenance']['weight_basis'],
            reason='Selected public performance synopsis with an explicit written-only scoring contract.')
        row['problem_description'] = (
            f"Create a complete written script and staging plan for the {row['year']} {title} public synopsis below. "
            'Solve only this selected synopsis; other problems in the archive file are out of scope. '
            'Include scene sequence, character actions, dialogue or silent action as appropriate, and proposed effects. '
            'Describe how effects could be produced; do not claim live performance, construction or testing occurred. '
            'This is a public-synopsis writing benchmark, not the member-only full problem or an official tournament score. '
            'Only published constraints apply. Unavailable private restrictions are not assumed. '
            'The following five written criteria are worth 20 benchmark points each:\n' +
            '\n'.join(f'{i}. {item}' for i, item in enumerate(requirements, 1)) + '\n\nSelected public synopsis:\n' + synopsis)
        row['total_points'] = 100
        row['gold_label']['grading_rubric'] = ev['rubric_path']
        row.setdefault('source_review', {})['main_synopsis_review'] = rubric['provenance']
        promoted.append(row['problem_id'])
    if not promoted:
        print('No unprocessed selected synopses; no files changed.')
        return
    put(path, rows)
    for base in [data, data / 'mini_data']:
        p = base / f'rules/{TRACK}/evaluation.json'
        rules = read(p)
        for key, (rp, rubric) in rubrics.items():
            dest = base / 'rubrics' / rp.name
            if base != data:
                put(dest, json.loads(json.dumps(rubric).replace('data/', 'data/mini_data/')))
            rules['scoring']['record_evaluator_overrides'][key] = 'rubric_llm_v1'
            rules['scoring']['record_rubric_overrides'][key] = dest.relative_to(ROOT).as_posix()
        current = rows if base == data else read(base / f'benchmarks/{TRACK}/benchmark.json')
        rules['scoring']['evaluation_status_counts'] = {s: sum(r['evaluation']['status'] == s for r in current) for s in {r['evaluation']['status'] for r in current}}
        put(p, rules)
    ip = data / 'benchmarks/index.json'
    index = read(ip)
    update_track_index(index, TRACK, rows)
    put(ip, index)
    sp = data / f'rubrics/task_scorecards/{TRACK}.json'
    cards = read(sp)
    cards['records'] = [scorecard(r, ROOT,
        read_json=lambda p: json.loads(staged[ROOT / p]) if ROOT / p in staged else read(ROOT / p),
        hash_file=lambda p: hashlib.sha256(staged[ROOT / p] if ROOT / p in staged else (ROOT / p).read_bytes()).hexdigest()) for r in rows]
    put(sp, cards)
    put(ROOT / 'tmp/main_odyssey_expansion_20260917.json', dict(promoted=promoted,
        scope='Written public-synopsis scripts only; no official live scores', mini_membership_changed=False, paid_calls=0))
    for path, before in originals.items():
        if (path.read_bytes() if path.exists() else None) != before:
            raise RuntimeError('Concurrent edit: ' + str(path))
    for path, value in staged.items():
        if originals[path] is not None:
            dest = backup / path.relative_to(ROOT)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(originals[path])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(value)
    print(json.dumps(dict(promoted=len(promoted), backup=str(backup))))


if __name__ == '__main__':
    main()
