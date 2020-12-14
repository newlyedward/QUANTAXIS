# coding=utf-8
#
# The MIT License (MIT)
#
# Copyright (c) 2016-2020 yutiansut/QUANTAXIS
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
import os
import webbrowser
from functools import lru_cache

try:
    from pyecharts import Kline
except:
    import pandas as pd
    import numpy as np
    from pyecharts import options as opts
    from pyecharts.commons.utils import JsCode
    from pyecharts.charts import Kline, Line, Bar, Grid

from QUANTAXIS.QAUtil.QALogs import QA_util_log_info
from QUANTAXIS.QAData.base_datastruct import _quotation_base


"""
0.5.1预计新增内容:


维护一个画图方法,之后可能会做成抽象基类


主要是画DataStruct的k线图, DataStruct加指标的图,以及回测框架的回测结果的图
"""

INIT_OPTS = opts.InitOpts(width='1360px', height='800px', page_title='QUANTAXIS')


class QA_Charts_Frame:
    """
    可视化数据，按主流软件图形，
        上部分为K线图，可以叠加各种指标,
        中间为成交量图，期货叠加持仓量
        下部分为指标幅图，
    """

    def __init__(self, ds: _quotation_base):
        """

        :param ds: 只有一个品种的ds
        """
        self.code = ds.code[0]
        self.ds = ds.select_code(self.code)  # 多个品种只返回第一个
        self.ohlc = self.ds.data.loc[:, ['open', 'close', 'low', 'high']].values.tolist()

        self.inst, self.freq = self.ds.type.split('_')
        if self.freq == 'day':
            self.datetime = self.ds.date.map(lambda x: str(x).split(' ')[0]).to_list()
        else:
            self.datetime = np.array(self.ds.datetime.map(str)).tolist()

        k_count = 72  # 一次显示7根K线，计算缩放的起始比例
        self.range_start = int(100 - k_count / len(self.datetime) * 100)

    @property
    @lru_cache()
    def k_line(self):
        # K线主图
        print(self.ds.code)
        k_line = (
            Kline(init_opts=INIT_OPTS)
                .add_xaxis(xaxis_data=self.datetime)
                .add_yaxis(
                series_name=self.code,
                y_axis=self.ohlc,
                itemstyle_opts=opts.ItemStyleOpts(
                    color="#ef232a",
                    color0="#14b143",
                    border_color="#ef232a",
                    border_color0="#14b143",
                ),
                markpoint_opts=opts.MarkPointOpts(
                    data=[
                        opts.MarkPointItem(type_="max", name="最大值"),
                        opts.MarkPointItem(type_="min", name="最小值"),
                    ]
                ),
            )
                .set_global_opts(
                title_opts=opts.TitleOpts(title=self.code, pos_left="0"),
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                    is_scale=True,
                    boundary_gap=False,
                    axisline_opts=opts.AxisLineOpts(is_on_zero=False),
                    splitline_opts=opts.SplitLineOpts(is_show=False),
                    split_number=20,
                    min_="dataMin",
                    max_="dataMax",
                ),
                yaxis_opts=opts.AxisOpts(
                    is_scale=True, splitline_opts=opts.SplitLineOpts(is_show=True)
                ),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="line"),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=True, type_="inside", range_start=self.range_start, range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True, pos_bottom="-1%", range_start=self.range_start, range_end=100
                    ),
                ],

            )
        )
        return k_line

    @property
    @lru_cache()
    def vol_bar(self):
        # 成交量辅图
        if self.inst == 'future':
            vol = self.ds.volume.map(lambda x: int(x * 100)).tolist()
        else:
            vol = self.ds.volume.map(int).tolist()

        vol_bar = (
            Bar(init_opts=INIT_OPTS)
            .add_xaxis(xaxis_data=self.datetime)
            .add_yaxis(
                series_name="Volume",
                y_axis=vol,
                label_opts=opts.LabelOpts(is_show=False),
            )
                .set_global_opts(
                xaxis_opts=opts.AxisOpts(
                    type_="category",
                ),
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="line"),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=True, type_="inside", range_start=self.range_start, range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True, pos_bottom="-1%", range_start=self.range_start, range_end=100
                    ),
                ],
            )
        )
        return vol_bar

    @property
    @lru_cache()
    def pos_line(self):
        pos = self.ds.position.map(int).tolist()
        pos_line = (
            Line(init_opts=INIT_OPTS)
            .add_xaxis(xaxis_data=self.datetime)
            .add_yaxis(
                series_name="Position",
                y_axis=pos,
                label_opts=opts.LabelOpts(is_show=False),
                is_symbol_show=False,
            )
                .set_global_opts(
                tooltip_opts=opts.TooltipOpts(trigger="axis", axis_pointer_type="line"),
                datazoom_opts=[
                    opts.DataZoomOpts(
                        is_show=True, type_="inside", range_start=self.range_start, range_end=100
                    ),
                    opts.DataZoomOpts(
                        is_show=True, pos_bottom="-1%", range_start=self.range_start, range_end=100
                    ),
                ],
            )
        )
        return pos_line


def plot_datastruct(_quotation_base, code=None):
    if code is None:
        path_name = '.' + os.sep + 'QA_' + _quotation_base.type + \
            '_codepackage_' + _quotation_base.if_fq + '.html'
        kline = Kline('CodePackage_' + _quotation_base.if_fq + '_' + _quotation_base.type,
                      width=1360, height=700, page_title='QUANTAXIS')

        data_splits = _quotation_base.splits()

        for i_ in range(len(data_splits)):
            data = []
            axis = []
            for dates, row in data_splits[i_].data.iterrows():
                open, high, low, close = row[1:5]
                datas = [open, close, low, high]
                axis.append(dates[0])
                data.append(datas)

            kline.add(_quotation_base.code[i_], axis, data, mark_point=[
                      "max", "min"], is_datazoom_show=True, datazoom_orient='horizontal')
        kline.render(path_name)
        webbrowser.open(path_name)
        QA_util_log_info('The Pic has been saved to your path: %s' % path_name)
    else:
        data = []
        axis = []
        for dates, row in _quotation_base.select_code(code).data.iterrows():
            open, high, low, close = row[1:5]
            datas = [open, close, low, high]
            axis.append(dates[0])
            data.append(datas)

        path_name = '.' + os.sep + 'QA_' + _quotation_base.type + \
            '_' + code + '_' + _quotation_base.if_fq + '.html'
        kline = Kline(code + '__' + _quotation_base.if_fq + '__' + _quotation_base.type,
                      width=1360, height=700, page_title='QUANTAXIS')
        kline.add(code, axis, data, mark_point=[
                  "max", "min"], is_datazoom_show=True, datazoom_orient='horizontal')
        kline.render(path_name)
        webbrowser.open(path_name)
        QA_util_log_info('The Pic has been saved to your path: %s' % path_name)


def QA_plot_save_html(pic_handle, path, if_open_web):
    """
    explanation:
        将绘图结果保存至指定位置		

    params:
        * pic_handle ->:
            meaning: 绘图
            type: null
            optional: [null]
        * path ->:
            meaning: 保存地址
            type: null
            optional: [null]
        * if_open_web ->:
            meaning: 是否调用浏览器打开
            type: bool
            optional: [null]

    return:
        None

    demonstrate:
        Not described

    output:
        Not described
    """

    pic_handle.render(path)
    if if_open_web:
        webbrowser.open(path)
    else:
        pass
    QA_util_log_info('The Pic has been saved to your path: %s' % path)

