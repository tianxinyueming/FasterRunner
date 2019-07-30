# -*- coding: utf-8 -*-
import time
import json
import os
from copy import deepcopy

from jinja2 import Environment, FileSystemLoader
from django.core.mail import EmailMultiAlternatives

from FasterRunner.settings import EMAIL_FROM, BASE_DIR
from fastrunner.utils.writeExcel import write_excel_log

def control_email(runresult, kwargs):
    if kwargs["strategy"] == '从不发送':
        return False
    elif kwargs["strategy"] == '始终发送':
        return True
    elif kwargs["strategy"] == '仅失败发送':
        if runresult["failures"] > 0:
            return True
    elif kwargs["strategy"] == '监控邮件':
        """
            新建一个monitor.json文件
            {
                task_name:{
                    "error_count": 0,
                    "error_message": ""
                }
            }
            runresultErrorMsg 是经过关键词过滤的执行结果，如果api调用失败后返回的报错信息内包含这些关键词，则将这个api的报错结果暂时记为空
            fail_count: 提前设置的错误此处阈值，超过则发送邮件

            1. 若 runresultErrorMsg == '' and error_message== '':  error_count = 0,error_message="" 不发送邮件
            2. 若 runresultErrorMsg == '' and error_message!= '':  error_count = 0,error_message="" 发送邮件
            3. 若 runresultErrorMsg != '' and error_message== '': error_count = 1, error_message=runresultErrorMsg，发送邮件
            4. 若 runresultErrorMsg != '' and error_message！= '' and error_message != runresultErrorMsg： error_count = 1,error_message=runresultErrorMsg 发送邮件
            5. 若 runresultErrorMsg！= '' and error_message != '' and error_message == runresultErrorMsg：
                3.1 若error_count <= fail_count: 发送邮件，error_count+1
                3.2 若error_count > fail_count: 不发送邮件，error_count+1
        """

        monitor_path = os.path.join(BASE_DIR, 'logs', 'monitor.json')
        if not os.path.isfile(monitor_path):
            all_json = {
                kwargs["task_name"]: {
                    "error_count": 0,
                    "error_message": ""
                }
            }
        else:
            with open(monitor_path, 'r', encoding='utf-8') as _json:
                all_json = json.load(_json)
            if kwargs["task_name"] not in all_json.keys():
                all_json[kwargs["task_name"]] = {
                        "error_count": 0,
                        "error_message": ""
                    }

        is_send_email = False
        last_json = all_json[kwargs["task_name"]]
        runresultErrorMsg = __filter_runresult(runresult, kwargs["self_error"])

        if runresultErrorMsg == '' and last_json["error_message"] == '':
            last_json["error_count"] = 0
            last_json["error_message"] = ""
            is_send_email = False
        elif runresultErrorMsg == '' and last_json["error_message"] != '':
            last_json["error_count"] = 0
            last_json["error_message"] = ""
            is_send_email = True
        elif runresultErrorMsg != '' and last_json["error_message"] == '':
            last_json["error_count"] = 1
            last_json["error_message"] = runresultErrorMsg
            is_send_email = True
        elif runresultErrorMsg != '' and last_json["error_message"] != '' and last_json["error_message"] != runresultErrorMsg:
            last_json["error_count"] = 1
            last_json["error_message"] = runresultErrorMsg
            is_send_email = True
        elif runresultErrorMsg != '' and last_json["error_message"] != '' and last_json["error_message"] == runresultErrorMsg:
            if last_json["error_count"] < int(kwargs["fail_count"]):
                is_send_email = True
            else:
                is_send_email = False
            last_json["error_count"] += 1

        all_json[kwargs["task_name"]] = last_json
        with open(monitor_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps(all_json))

        return is_send_email

    else:
        return False


def send_result_email(send_subject, send_to, send_cc, send_text_content=None, send_html_content=None, send_file_path=[], from_email=EMAIL_FROM):
    """
    :param send_subject: str
    :param send_to: list
    :param send_cc: list
    :param send_text_content: str
    :param send_html_content: html
    :param from_email: str
    :param send_file_path: list
    :return: bool
    """
    msg = EmailMultiAlternatives(subject=send_subject, from_email=from_email, to=send_to, cc=send_cc)
    if send_text_content:
        msg.attach_alternative(send_text_content, 'text/plain')
    if send_html_content:
        msg.attach_alternative(send_html_content, 'text/html')
    if send_file_path:
        for file_path in send_file_path:
            msg.attach_file(file_path)
    send_status = msg.send()
    return send_status


def prepare_email_content(runresult, subject_name):
    """
    :param runresult: 生成的简要分析结果
    :param subject_name: html名称
    :return: email conetnt
    """
    batch_result = {}
    batch_result['report_name'] = subject_name
    batch_result['time_start'] = runresult["start_time"]
    batch_result['testsRun'] = runresult["testsRun"]
    batch_result['failures'] = runresult["failures"]
    batch_result['successes'] = runresult["successes"]
    batch_result['tests'] = runresult["tests"]
    batch_result['error_list'] = runresult["error_list"]

    report_template = Environment(loader=FileSystemLoader(BASE_DIR)).get_template('./templates/email_report.html')

    return report_template.render(batch_result)


def parser_runresult(sample_summary):
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
    runresult = {
        "testsRun": testsRun,
        "failures": failures,
        "successes": successes,
        "tests": tests,
        "error_list": error_list,
        "start_time": time.strftime('%Y-%m-%d %H %M %S', time.localtime(sample_summary[0]["time"]["start_at"]))
    }
    return runresult


def prepare_email_file(sample_summary):
    """
    :param sample_summary: list
    :return: file path list
    """
    # 汇总报告
    summary_report = sample_summary[0]
    for index, summary in enumerate(sample_summary):
        if index > 0:
            summary_report["success"] = summary["success"] if not summary["success"] else summary_report["success"]
            summary_report["stat"]["testsRun"] += summary["stat"]["testsRun"]
            summary_report["stat"]["failures"] += summary["stat"]["failures"]
            summary_report["stat"]["skipped"] += summary["stat"]["skipped"]
            summary_report["stat"]["successes"] += summary["stat"]["successes"]
            summary_report["stat"]["expectedFailures"] += summary["stat"]["expectedFailures"]
            summary_report["stat"]["unexpectedSuccesses"] += summary["stat"]["unexpectedSuccesses"]
            summary_report["time"]["duration"] += summary["time"]["duration"]
            summary_report["details"].extend(summary["details"])
    file_path = write_excel_log(summary_report)
    return [file_path]


def __filter_runresult(runresult, self_error_list):
    runresultErrorMsg = ''
    if runresult["error_list"]:
        for err in runresult["error_list"]:
            runresultErrorMsg += __is_self_error(err["content"].strip(), self_error_list)
    return runresultErrorMsg


def __is_self_error(error_content, self_error_list):
    if error_content and self_error_list:
        for error_message in self_error_list:
            if error_message in error_content:
                return ""
    return error_content
