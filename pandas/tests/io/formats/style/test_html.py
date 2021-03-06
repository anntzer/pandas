from textwrap import dedent

import pytest

from pandas import DataFrame

jinja2 = pytest.importorskip("jinja2")
from pandas.io.formats.style import Styler

loader = jinja2.PackageLoader("pandas", "io/formats/templates")
env = jinja2.Environment(loader=loader, trim_blocks=True)


@pytest.fixture
def styler():
    return Styler(DataFrame([[2.61], [2.69]], index=["a", "b"], columns=["A"]))


@pytest.fixture
def tpl_style():
    return env.get_template("html_style.tpl")


@pytest.fixture
def tpl_table():
    return env.get_template("html_table.tpl")


def test_html_template_extends_options():
    # make sure if templates are edited tests are updated as are setup fixtures
    # to understand the dependency
    with open("pandas/io/formats/templates/html.tpl") as file:
        result = file.read()
    assert '{% include "html_style.tpl" %}' in result
    assert '{% include "html_table.tpl" %}' in result


def test_exclude_styles(styler):
    result = styler.to_html(exclude_styles=True, doctype_html=True)
    expected = dedent(
        """\
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        </head>
        <body>
        <table>
          <thead>
            <tr>
              <th >&nbsp;</th>
              <th >A</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th >a</th>
              <td >2.610000</td>
            </tr>
            <tr>
              <th >b</th>
              <td >2.690000</td>
            </tr>
          </tbody>
        </table>
        </body>
        </html>
        """
    )
    assert result == expected


def test_w3_html_format(styler):
    styler.set_uuid("").set_table_styles(
        [{"selector": "th", "props": "att2:v2;"}]
    ).applymap(lambda x: "att1:v1;").set_table_attributes(
        'class="my-cls1" style="attr3:v3;"'
    ).set_td_classes(
        DataFrame(["my-cls2"], index=["a"], columns=["A"])
    ).format(
        "{:.1f}"
    ).set_caption(
        "A comprehensive test"
    )
    expected = dedent(
        """\
        <style type="text/css">
        #T_ th {
          att2: v2;
        }
        #T_row0_col0, #T_row1_col0 {
          att1: v1;
        }
        </style>
        <table id="T_" class="my-cls1" style="attr3:v3;">
          <caption>A comprehensive test</caption>
          <thead>
            <tr>
              <th class="blank level0" >&nbsp;</th>
              <th class="col_heading level0 col0" >A</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th id="T_level0_row0" class="row_heading level0 row0" >a</th>
              <td id="T_row0_col0" class="data row0 col0 my-cls2" >2.6</td>
            </tr>
            <tr>
              <th id="T_level0_row1" class="row_heading level0 row1" >b</th>
              <td id="T_row1_col0" class="data row1 col0" >2.7</td>
            </tr>
          </tbody>
        </table>
        """
    )
    assert expected == styler.render()


def test_colspan_w3():
    # GH 36223
    df = DataFrame(data=[[1, 2]], columns=[["l0", "l0"], ["l1a", "l1b"]])
    styler = Styler(df, uuid="_", cell_ids=False)
    assert '<th class="col_heading level0 col0" colspan="2">l0</th>' in styler.render()


def test_rowspan_w3():
    # GH 38533
    df = DataFrame(data=[[1, 2]], index=[["l0", "l0"], ["l1a", "l1b"]])
    styler = Styler(df, uuid="_", cell_ids=False)
    assert (
        '<th id="T___level0_row0" class="row_heading '
        'level0 row0" rowspan="2">l0</th>' in styler.render()
    )


def test_styles(styler):
    styler.set_uuid("abc_")
    styler.set_table_styles([{"selector": "td", "props": "color: red;"}])
    result = styler.to_html(doctype_html=True)
    expected = dedent(
        """\
        <!DOCTYPE html>
        <html>
        <head>
        <meta charset="utf-8">
        <style type="text/css">
        #T_abc_ td {
          color: red;
        }
        </style>
        </head>
        <body>
        <table id="T_abc_">
          <thead>
            <tr>
              <th class="blank level0" >&nbsp;</th>
              <th class="col_heading level0 col0" >A</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th id="T_abc_level0_row0" class="row_heading level0 row0" >a</th>
              <td id="T_abc_row0_col0" class="data row0 col0" >2.610000</td>
            </tr>
            <tr>
              <th id="T_abc_level0_row1" class="row_heading level0 row1" >b</th>
              <td id="T_abc_row1_col0" class="data row1 col0" >2.690000</td>
            </tr>
          </tbody>
        </table>
        </body>
        </html>
        """
    )
    assert result == expected


def test_doctype(styler):
    result = styler.to_html(doctype_html=False)
    assert "<html>" not in result
    assert "<body>" not in result
    assert "<!DOCTYPE html>" not in result
    assert "<head>" not in result


def test_block_names(tpl_style, tpl_table):
    # catch accidental removal of a block
    expected_style = {
        "before_style",
        "style",
        "table_styles",
        "before_cellstyle",
        "cellstyle",
    }
    expected_table = {
        "before_table",
        "table",
        "caption",
        "thead",
        "tbody",
        "after_table",
        "before_head_rows",
        "head_tr",
        "after_head_rows",
        "before_rows",
        "tr",
        "after_rows",
    }
    result1 = set(tpl_style.blocks)
    assert result1 == expected_style

    result2 = set(tpl_table.blocks)
    assert result2 == expected_table


def test_from_custom_template(tmpdir):
    p = tmpdir.mkdir("templates").join("myhtml.tpl")
    p.write(
        dedent(
            """\
        {% extends "html.tpl" %}
        {% block table %}
        <h1>{{ table_title|default("My Table") }}</h1>
        {{ super() }}
        {% endblock table %}"""
        )
    )
    result = Styler.from_custom_template(str(tmpdir.join("templates")), "myhtml.tpl")
    assert issubclass(result, Styler)
    assert result.env is not Styler.env
    assert result.template_html is not Styler.template_html
    styler = result(DataFrame({"A": [1, 2]}))
    assert styler.render()
