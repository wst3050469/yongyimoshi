#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""全自动内容发布流水线 v5.7.0 — 挖词→生成→评分→发布 一键串联"""
import os, json, time, uuid
from datetime import datetime
from typing import Dict, List, Optional

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
JOBS_FILE = os.path.join(DATA_DIR, 'publish_jobs.json')
os.makedirs(DATA_DIR, exist_ok=True)


class PublishPipeline:
    """全自动发布流水线：挖词→生成→评分→发布"""

    def __init__(self):
        self.jobs = self._load_jobs()

    def _load_jobs(self) -> List[Dict]:
        try:
            if os.path.exists(JOBS_FILE):
                with open(JOBS_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except:
            pass
        return []

    def _save_jobs(self):
        with open(JOBS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.jobs, f, ensure_ascii=False, indent=2)

    def start(self, platforms: List[str] = None, seed_keywords: List[str] = None,
              content_type: str = "auto", auto_publish: bool = True,
              max_count: int = 3) -> Dict:
        """启动全自动流水线

        Args:
            platforms: 目标平台列表，默认douyin
            seed_keywords: 种子关键词，默认使用内置
            content_type: 内容类型 (auto=自动判断, script=脚本, article=文章)
            auto_publish: 是否自动发布 (False=只生成不发布)
            max_count: 最多生成几条内容

        Returns:
            job字典，含job_id用于查询进度
        """
        if platforms is None:
            platforms = ['douyin']
        if seed_keywords is None:
            seed_keywords = ['无机磨石', '金磨石', '环氧磨石', '磨石地坪']

        job_id = str(uuid.uuid4())[:12]
        job = {
            'job_id': job_id,
            'status': 'starting',
            'platforms': platforms,
            'seed_keywords': seed_keywords,
            'auto_publish': auto_publish,
            'created_at': datetime.now().isoformat(),
            'steps': [], 'results': [],
            'total_time_s': 0
        }
        self.jobs.append(job)
        self._save_jobs()

        start_time = time.time()

        try:
            # === Step 1: 关键词挖掘 ===
            job['status'] = 'mining'
            job['steps'].append({'step': 'mining', 'status': 'running', 'started': datetime.now().isoformat()})
            self._save_jobs()

            from docs.keyword_miner import KeywordMiner
            miner = KeywordMiner()
            mine_result = miner.deep_mine(
                seed_words=seed_keywords,
                platforms=['douyin', 'xhs', 'baidu'],
                rounds=['semantic', 'longtail', 'questions']
            )

            # 取挖掘到的长尾关键词作为发布候选
            keywords_pool = miner.get_mined_pool()
            candidate_keywords = [k for k in keywords_pool if k.get('heat_score', 0) >= 2][:max_count]

            job['steps'][-1]['status'] = 'done'
            job['steps'][-1]['keywords_found'] = len(keywords_pool)
            job['steps'][-1]['candidates'] = len(candidate_keywords)
            self._save_jobs()

            if not candidate_keywords:
                # 回退：用种子关键词
                candidate_keywords = [{'word': kw, 'category': '种子词', 'heat_score': 2}
                                      for kw in seed_keywords[:max_count]]

            # === Step 2: 内容生成 & AI评分 ===
            job['status'] = 'generating'
            job['steps'].append({'step': 'generating', 'status': 'running', 'started': datetime.now().isoformat()})
            self._save_jobs()

            from docs.marketing_system import KeywordEngine
            engine = KeywordEngine()

            # 平台→方法映射
            PLATFORM_METHOD = {
                'douyin': 'gen_video', 'xhs': 'gen_xhs', 'zhihu': 'gen_zhihu',
                'weibo': 'gen_weibo', 'baijiahao': 'gen_baijiahao', 'wechat': 'gen_article'
            }

            generated_contents = []
            for kw_info in candidate_keywords[:max_count]:
                kw = kw_info['word']
                contents = {}
                for p in platforms:
                    method_name = PLATFORM_METHOD.get(p, 'gen_video')
                    try:
                        gen = getattr(engine, method_name)(kw, style='professional')
                        # gen_video等所有方法返回纯字符串
                        content = gen if isinstance(gen, str) else str(gen)
                        if content:
                            contents[p] = {'content': content, 'platform': p}
                    except Exception as e:
                        contents[p] = {'content': f'[{kw}] 生成失败: {e}', 'error': str(e)}

                # AI评分
                score = None
                try:
                    from docs.ai_quality import AIQualityEngine
                    aiq = AIQualityEngine()
                    for p, c in contents.items():
                        score_result = aiq.score(c.get('content', ''))
                        c['ai_score'] = score_result
                except:
                    pass

                generated_contents.append({
                    'keyword': kw,
                    'contents': contents,
                    'ai_score': score
                })

            job['steps'][-1]['status'] = 'done'
            job['steps'][-1]['generated'] = len(generated_contents)
            self._save_jobs()

            # === Step 3: 自动发布 ===
            if auto_publish:
                job['status'] = 'publishing'
                job['steps'].append({'step': 'publishing', 'status': 'running', 'started': datetime.now().isoformat()})
                self._save_jobs()

                from docs.auto_publisher import AutoPublisher
                publisher = AutoPublisher()

                publish_results = []
                for gen in generated_contents:
                    for platform in platforms:
                        content_data = gen['contents'].get(platform, {})
                        if content_data.get('content'):
                            result = publisher.publish(
                                platform=platform,
                                title=gen['keyword'],
                                content=content_data['content'],
                                dry_run=not auto_publish
                            )
                            result['keyword'] = gen['keyword']
                            publish_results.append(result)
                            time.sleep(3)  # 平台间间隔

                job['results'] = publish_results
                job['steps'][-1]['status'] = 'done'
                job['steps'][-1]['published'] = len([r for r in publish_results if r.get('success')])
                job['steps'][-1]['failed'] = len([r for r in publish_results if not r.get('success')])

                # 记录发布历史
                try:
                    from docs.wechat_publisher import PublishedStore
                    store = PublishedStore()
                    for r in publish_results:
                        if r.get('success'):
                            store.add(job_id, r.get('platform', 'unknown'), r)
                except:
                    pass

            job['status'] = 'done'
            job['total_time_s'] = round(time.time() - start_time, 1)

        except Exception as e:
            job['status'] = 'error'
            job['error'] = str(e)

        job['completed_at'] = datetime.now().isoformat()
        job['total_time_s'] = round(time.time() - start_time, 1)
        self._save_jobs()

        return job

    def get_status(self, job_id: str) -> Optional[Dict]:
        """查询流水线进度"""
        for job in self.jobs:
            if job.get('job_id') == job_id:
                return job
        return None

    def get_all_jobs(self, limit: int = 20) -> List[Dict]:
        return list(reversed(self.jobs[-limit:]))

    def get_stats(self) -> Dict:
        """流水线统计"""
        total = len(self.jobs)
        done = len([j for j in self.jobs if j.get('status') == 'done'])
        errors = len([j for j in self.jobs if j.get('status') == 'error'])
        total_published = 0
        for j in self.jobs:
            for r in j.get('results', []):
                if r.get('success'):
                    total_published += 1
        return {
            'total_jobs': total, 'done': done, 'errors': errors,
            'total_published': total_published
        }


# 全局单例
publish_pipeline = PublishPipeline()
