# -*- coding: utf-8 -*-
import time
import json
from copy import deepcopy

from jinja2 import Environment, FileSystemLoader
from django.core.mail import EmailMultiAlternatives

from FasterRunner.settings import EMAIL_FROM, BASE_DIR


def send_result_email(send_subject, send_to, send_cc, send_text_content=None, send_html_content=None, from_email=EMAIL_FROM):
    """
    :param send_subject: str
    :param send_to: list
    :param send_cc: list
    :param send_text_content: str
    :param send_html_content: html
    :param from_email: str
    :return: bool
    """
    msg = EmailMultiAlternatives(subject=send_subject, from_email=from_email, to=send_to, cc=send_cc)
    if send_text_content:
        msg.attach_alternative(send_text_content, 'text/plain')
    if send_html_content:
        msg.attach_alternative(send_html_content, 'text/html')
    send_status = msg.send()
    return send_status


def prepare_email_content(sample_summary, subject_name):
    """
    :param sample_summary: list 定时任务生成的报告列表
    :param subject_name: html名称
    :return: email conetnt
    """
    testsRun = 0
    failures = 0
    successes = 0
    tests = []
    error_list = []
    for summary in sample_summary:
        test = {}
        test["status"] = 'success' if summary["success"] else 'error'
        test['name'] = summary["name"]
        test['link'] = test['name']
        error_response_content = ''
        for deatil in summary["details"]:
            testsRun += len(summary["details"])
            if not deatil["success"]:
                failures += 1
                error_api = deatil["records"][-1]
                error_response = error_api["meta_data"]["response"]
                error_response_content += error_response["content"] + '\n' \
                    if 'content' in error_response.keys() and error_response["content"] is not None else ''

        if test["status"] == 'error':
            err_msg = {}
            err_msg["proj"] = test['name']
            err_msg["content"] = error_response_content
            error_list.append(deepcopy(err_msg))

        tests.append(deepcopy(test))

    successes = testsRun - failures

    batch_result = {}
    batch_result['report_name'] = subject_name
    batch_result['time_start'] = time.strftime('%Y-%m-%d %H %M %S', time.localtime(sample_summary[0]["time"]["start_at"]))
    batch_result['testsRun'] = testsRun
    batch_result['failures'] = failures
    batch_result['successes'] = successes
    batch_result['tests'] = tests
    batch_result['error_list'] = error_list

    report_template = Environment(loader=FileSystemLoader(BASE_DIR)).get_template('./templates/email_report.html')

    return report_template.render(batch_result)

    # # 汇总报告
    # summary_report = sample_summary[0]
    # for index, summary in enumerate(sample_summary):
    #     if index > 0:
    #         summary_report["success"] = summary["success"] if not summary["success"] else summary_report["success"]
    #         summary_report["stat"]["testsRun"] += summary["stat"]["testsRun"]
    #         summary_report["stat"]["failures"] += summary["stat"]["failures"]
    #         summary_report["stat"]["skipped"] += summary["stat"]["skipped"]
    #         summary_report["stat"]["successes"] += summary["stat"]["successes"]
    #         summary_report["stat"]["expectedFailures"] += summary["stat"]["expectedFailures"]
    #         summary_report["stat"]["unexpectedSuccesses"] += summary["stat"]["unexpectedSuccesses"]
    #         summary_report["time"]["duration"] += summary["time"]["duration"]
    #         summary_report["details"].extend(summary["details"])