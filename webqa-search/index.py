import json
import os

from jina.flow import Flow


def read_data(fn):
    items = {}
    with open(fn, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            if item['content'] == '':
                continue
            if item['qid'] not in items.keys():
                items[item['qid']] = {}
                items[item['qid']]['title'] = item['title']
                items[item['qid']]['answers'] = [{'answer_id': item['answer_id'], 'content': item['content']}]
            else:
                items[item['qid']]['answers'].append({'answer_id': item['answer_id'], 'content': item['content']})

    result = []
    for qid, value in items.items():
        value['qid'] = qid
        result.append(("{}".format(json.dumps(value, ensure_ascii=False))).encode("utf-8"))
    print(f'total docs: {len(result)}')

    for item in result[:100]:
        yield item


def main():
    workspace_path = '/tmp/jina/webqa'
    os.environ['TMP_WORKSPACE'] = workspace_path
    data_fn = os.path.join(workspace_path, "web_text_zh_valid.json")
    flow = Flow().add(
        name='title_extractor',
        yaml_path='images/title_extractor/title_extractor.yml'
    ).add(
        name='title_meta_doc_indexer',
        yaml_path='images/title_meta_doc_indexer/title_meta_doc_indexer.yml',
        needs='gateway',
        replicas=1,
    ).add(
        name='title_encoder',
        image='jinaai/hub.executors.encoders.nlp.transformers-hitscir',
        needs='title_extractor',
        timeout_ready=1000000,
        replicas=2
    ).add(
        name='title_compound_chunk_indexer',
        yaml_path='images/title_compound_chunk_indexer/title_compound_chunk_indexer.yml',
        needs='title_encoder',
        replicas=1,
    ).join(['title_compound_chunk_indexer', 'title_meta_doc_indexer'])
    with flow.build() as f:
        f.index(raw_bytes=read_data(data_fn), batch_size=8, prefetch=10)


if __name__ == '__main__':
    main()