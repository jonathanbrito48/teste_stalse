import pandas as pd
import datetime as dt
import json


df = pd.read_csv("data/raw/Technical Support Dataset.csv" ,sep=',')


def transform(data):
    # renomear colunas
    df.columns = [col.replace(' ', '_').lower() for col in df.columns]    
    
    # Parse de data
    for data_columns in df.columns[[7,8,9,12,14]]:
        df[f'{data_columns}'] = pd.to_datetime(df[f'{data_columns}'],yearfirst=True)
    
    # Metricas 
    metrics = []

    ## Metricas de contagem
    for groups in df.columns[[0,2,4,5,-5,-4]]:
        metrics.append({f'{groups}_count':df.value_counts(groups).sort_values(ascending=False).to_dict()})

    ## Média de SlAs
    df['sla'] = (df['close_time'] - df['created_time']).dt.days
    for sla_cat in df.columns[[4,5,6,-5,-6]]:
        metrics.append({f'{sla_cat}_sla_mean':df.groupby(sla_cat)[['sla']].mean().round(2).to_dict(orient='index')})

    ## Tickets por mês agrupados
    df['ano_mes_ticket'] = df['created_time'].dt.strftime('%Y-%m')
    for groups in df.columns[[4,5,6,-5,-6]]:
        metrics.append({f'size_tickets_{groups}':df.groupby(['ano_mes_ticket',f'{groups}']).size().unstack().fillna(0).astype(int).to_dict('index')})

    #Dump json
    with open('data/processed/metrics.json','w') as f:
        json.dump(metrics, f, indent=4)

    return print('ETL Processado!')


transform(df)