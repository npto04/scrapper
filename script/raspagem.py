# -*- coding: utf-8 -*-

"""Implemente um web scraper (robot) em qualquer linguagem para extrair os dados de apartamentos que estão a venda na cidade de Natal. Seu código deverá gerar um arquivo CSV como resultado da extração. Submeta o código e o arquivo CSV resultante"""

# Imports
import requests
import pandas as pd
from bs4 import BeautifulSoup
import datetime as dt
from pathlib import Path
import os
import re
import time

# Vars
base_url = 'https://imoveis.trovit.com.br/index.php/cod.search_homes/type.1/what_d.apartamento/sug.0/isUserSearch.1/order_by.relevance/city.Natal/page.{}'
user_agent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.62 Safari/537.36"
dir = Path.cwd() / 'data'
print(dir)


def scrape(content: bytes) -> dict:
    """ Extrai apartamentos de uma página html
        Params:
        -----
        content : bytes
            Conteúdo da página html
        Returns:
        -----
        aptos : dict
            Conjunto de apartamentos com seus dados estruturado em um dicionario
    """

    aptos = {}

    aptos['endereco'] = []

    aptos['preco'] = []

    aptos['quartos'] = []

    aptos['banheiros'] = []

    aptos['area'] = []

    # Parser
    soup = BeautifulSoup(content, 'html.parser')

    # Extrair todos os anúncios
    for estate in soup.find_all(class_='snippet-content-main'):
        if estate.find(class_='actual-price'):
            # extrair endereço
            aptos['endereco'].append(
                estate.find(class_='address').text.strip())

            # extrair preço
            aptos['preco'].append(estate.find(
                class_='actual-price').text.replace('R$', '').replace('.', ''))

            try:
                # extrair quartos
                aptos['quartos'].append(estate.find(
                    class_='item-property item-rooms').text.split()[0])
            except:
                aptos['quartos'].append(None)

            try:
                # extrair banheiros
                aptos['banheiros'].append(estate.find(
                    class_='item-property item-baths').text.split()[0])
            except:
                aptos['banheiros'].append(None)

            try:
                # extrair área
                aptos['area'].append(re.search(r"^\d*",
                                               estate.find(class_='item-property item-size').text.strip()).group())
            except:
                aptos['area'].append(None)

    return aptos


def save(aptos: dict) -> None:
    """ Insere apartamentos no arquivo
        Params:
        -----
        aptos : dict
            Conjunto de apartamentos com seus dados estruturado em um dicionario
        Returns:
        -----
        None
    """
    # Ler arquivo
    file_path = dir / "trovit_apto_{}.csv".format(dt.date.today().isoformat())
    try:
        df = pd.read_csv(os.fspath(file_path))
    except:
        # Novo arquivo
        df = pd.DataFrame()
    # Inserir dados
    aptos_df = pd.DataFrame(aptos)
    try:
        if df.empty:
            aptos_df.to_csv(file_path, index=False)
        else:
            df = pd.concat([df, aptos_df])
            df.to_csv(file_path, index=False)
    except Exception as e:
        print(e)
        print('Nao pode salvar o arquivo: {}'.format(file_path))


def paginate(url: str) -> int:
    """ Itera sobre as páginas se url permite, 
    recuperando as informações disponíveis
        Returns:
        -----
        pg_nums : int
            Numero de paginas raspadas
    """
    pg_nums = 1
    while True:
        time.sleep(10)
        try:
            print(url.format(pg_nums))
            resposta = requests.get(url.format(pg_nums),
                                    headers={'user-agent': user_agent})
            if resposta.status_code != 200:
                raise Exception("Sem resposta")
            paginas = scrape(resposta.content)
            if not paginas:
                raise Exception("Sem mais apartamentos")
        except Exception as e:
            print(e)
            print('Fim de raspagem.')
            break
        # Armazenando valores
        save(paginas)
        pg_nums += 1
        #break ###
    return pg_nums


if __name__ == "__main__":
    print('Iniciando raspagem no trovit')
    pg_nums = paginate(base_url)
    print('Raspagem finalizada. {} páginas raspadas.'.format(pg_nums))
    print('Arquivo salvo em: {}'.format(dir))
    print('Arquivo: trovit_apto_{}.csv'.format(dt.date.today().isoformat()))
