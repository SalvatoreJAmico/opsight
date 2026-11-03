"""Offline regressions for real schemas, format parity and unsuitable data."""
import os
os.environ.setdefault("APP_ENV", "dev")
os.environ.setdefault("APP_VERSION", "test")
os.environ.setdefault("PORT", "8000")
os.environ.setdefault("UPLOAD_ACCESS_CODE", "test-access-code")
os.environ.setdefault("PERSISTENCE_MODE", "json")
os.environ.setdefault("STORAGE_PATH", "data/test-records.json")
os.environ.setdefault("LOG_LEVEL", "INFO")
os.environ.setdefault("ALLOW_LOCAL_FALLBACK", "true")
os.environ.setdefault("API_BASE_URL", "http://api-test.local:8000")
os.environ.setdefault("INPUT_SOURCE_PATH", "data/opsight_sample_sales.csv")
os.environ.setdefault("PIPELINE_SUMMARY_PATH", "reports/pipeline_run_summary.json")
import json
from unittest.mock import patch
import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient
from modules.adapter.adapter import adapt_records
import modules.api.app as api
from modules.api import session_state
from modules.api.chart_schema import schema_for

@pytest.fixture
def chart_client(tmp_path, monkeypatch):
    from types import SimpleNamespace
    path = tmp_path / 'records.json'
    monkeypatch.setattr(api, 'StorageConfig', lambda: SimpleNamespace(storage_path=str(path)))
    import modules.visualization.plots as plots
    monkeypatch.setattr(plots, 'PLOT_DIR', str(tmp_path / 'plots'))
    session_state.reset_session_state()
    def seed(frame, dataset='sales_sql'):
        records = adapt_records(frame)
        path.write_text(json.dumps(records, default=str))
        session_state.set_active_dataset(dataset)
        session_state.set_pipeline_status("completed")
    yield TestClient(api.app), seed
    session_state.reset_session_state()

def orders():
    return pd.DataFrame({'OrderID':[1,2,3], 'OrderDate':['2026-01-01','2026-01-02','2026-01-03'],
                         'Freight':[12.0,31.0,7.5], 'ShipCity':['Plano','York','Plano'],
                         'ShipRegion':[None,'IL',None]})

def test_northwind_all_chart_routes(chart_client):
    client, seed = chart_client
    seed(orders())
    overview = client.get('/charts/overview').json()
    assert overview['assignment_analysis']['target_variable'] == 'freight'
    assert overview['assignment_analysis']['target_options'] == ['freight']
    assert overview['missing_by_column']['shipregion'] == 2
    assert 'Sales' not in overview['fields']
    for chart in ['histogram','boxplot','bar-category','scatter','grouped-comparison','grouped-boxplot','time-line']:
        compare = 'Timestamp' if chart == 'time-line' else 'shipcity'
        result = client.get(f'/charts/{chart}', params={'target_variable':'freight','compare_variable':compare})
        assert result.status_code == 200, result.text
        assert result.json()['image'].endswith('.png')
    assert client.get('/charts/histogram',params={'target_variable':'Sales'}).status_code == 422

@pytest.mark.parametrize('fmt',['csv','json','parquet','xlsx','sql'])
def test_equivalent_supported_format_schemas(chart_client,tmp_path,fmt):
    client, seed = chart_client
    frame = orders()
    path = tmp_path / ('source.'+fmt)
    if fmt=='csv': frame.to_csv(path,index=False); loaded=pd.read_csv(path)
    elif fmt=='json': frame.to_json(path,orient='records'); loaded=pd.read_json(path)
    elif fmt=='parquet': frame.to_parquet(path,index=False); loaded=pd.read_parquet(path)
    elif fmt=='xlsx': frame.to_excel(path,index=False); loaded=pd.read_excel(path)
    else:
        # SQL transport remains mocked: no database or credentials required.
        from modules.ingestion.ingestion import _load_from_sql
        with patch('sqlalchemy.create_engine') as engine, patch('pandas.read_sql_query',return_value=frame):
            loaded=_load_from_sql('Northwind','dbo','Orders','sqlite://')
    seed(loaded)
    summary=client.get('/charts/overview')
    assert summary.status_code==200
    assert summary.json()['assignment_analysis']['target_options']==['freight']
    assert client.get('/charts/histogram',params={'target_variable':'freight'}).status_code==200

def test_categorical_only_has_counts_not_numeric_charts(chart_client):
    client,seed=chart_client
    seed(orders().drop(columns='Freight'))
    body=client.get('/charts/overview').json()
    assert body['assignment_analysis']['target_options']==[]
    assert body['assignment_analysis']['target_variable'] is None
    assert client.get('/charts/bar-category',params={'compare_variable':'shipcity'}).status_code==200
    assert client.get('/charts/histogram',params={'target_variable':'shipcity'}).status_code==422

def test_dataset_switch_resets_variables():
    session_state.set_active_dataset('sales_csv')
    session_state.set_selected_variables('Sales',['Profit'])
    session_state.set_active_dataset('sales_sql')
    assert session_state.get_session_state()['selected_variables']=={'target':None,'compare':[]}

def test_unusable_numeric_and_no_overlap_fail_clearly(monkeypatch):
    client=TestClient(api.app)
    df=pd.DataFrame({'sales':[np.inf,np.nan],'profit':[1,2]})
    monkeypatch.setattr(api,'get_chart_dataframe',lambda:df.copy())
    response=client.get('/charts/histogram',params={'target_variable':'Sales'})
    assert response.status_code==422
    assert 'finite' in response.json()['detail']
    df=pd.DataFrame({'sales':[1,np.nan],'profit':[np.nan,2]})
    assert client.get('/charts/scatter').status_code==422

def test_empty_dataset(chart_client):
    client,seed=chart_client
    seed(orders().iloc[:0])
    assert client.get('/charts/overview').status_code==422
    assert client.get('/charts/histogram').status_code==422

def test_numeric_id_and_bool_not_suggested_as_measurement():
    fields,kinds=schema_for(pd.DataFrame({'entity_id':[1,2],'flag':[True,False],'value':[2.,4.]}))
    assert 'entity_id' not in fields
    assert kinds['flag']=='categorical'
    assert kinds['value']=='numeric'


def test_dirty_dates_remain_date_and_plot_valid_rows(chart_client):
    client, seed = chart_client
    frame = orders()
    frame.loc[1, 'OrderDate'] = 'not a date'
    seed(frame)
    overview = client.get('/charts/overview').json()
    assert overview['field_types']['Timestamp'] == 'date'
    assert overview['date_summary'][0]['count'] == 2
    assert overview['date_summary'][0]['missing'] == 1
    response = client.get('/charts/time-line', params={'target_variable':'freight','compare_variable':'Timestamp'})
    assert response.status_code == 200, response.text


def test_categorical_sales_is_not_a_numeric_target(chart_client):
    client, seed = chart_client
    frame = orders().rename(columns={'ShipCity':'Sales'})
    seed(frame)
    response = client.get('/charts/overview')
    assert response.status_code == 200, response.text
    body = response.json()
    assert body['assignment_analysis']['target_variable'] == 'freight'
    assert 'Sales' not in body['assignment_analysis']['target_options']
    assert body['field_types']['Sales'] == 'categorical'
    assert 'mean' not in body


@pytest.mark.parametrize('status', ['not_run', 'running', 'failed'])
def test_unprocessed_dataset_cannot_display_previous_records(chart_client, status):
    client, seed = chart_client
    seed(orders(), 'sales_sql')
    session_state.set_active_dataset('sales_csv')
    session_state.set_pipeline_status(status)
    for route in ['overview','histogram','boxplot','scatter','bar-category','grouped-comparison','grouped-boxplot','time-line']:
        result = client.get('/charts/' + route, params={'target_variable':'freight','compare_variable':'shipcity'})
        assert result.status_code == 422, (route,result.text)
        assert 'completed processing' in result.json()['detail']
