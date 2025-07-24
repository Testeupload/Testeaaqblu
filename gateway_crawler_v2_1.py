import requests
from bs4 import BeautifulSoup
import re
import json
import time
import csv
from urllib.parse import urlparse, urljoin
from collections import deque
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging
from datetime import datetime
import argparse
import sys

# Configuração de logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

class GatewayCrawlerV2:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Definição expandida de gateways e suas assinaturas
        # Adicionando mais gateways globais/internacionais e refinando assinaturas
        self.gateways = {
            "Stripe": {
                "keywords": ["stripe.com", "js.stripe.com", "data-stripe", "pk_live", "pk_test", "stripe-js", "stripe-payment", "stripe-checkout"],
                "scripts": ["js.stripe.com/v3/", "checkout.stripe.com", "js.stripe.com/v2/"],
                "forms": ["stripe-payment-form", "stripe-form"],
                "meta": ["stripe-publishable-key", "stripe-key"],
                "css_classes": ["stripe-button", "stripe-checkout"],
                "api_endpoints": ["/stripe/", "/api/stripe/"]
            },
            "PayPal": {
                "keywords": ["paypal.com", "paypalobjects.com", "data-paypal", "paypal-button", "paypal-checkout", "paypal-express"],
                "scripts": ["www.paypalobjects.com/api/checkout.js", "js.paypal.com", "paypal.com/sdk/js"],
                "forms": ["paypal-payment-form", "paypal-form"],
                "meta": ["paypal-client-id", "paypal-merchant-id"],
                "css_classes": ["paypal-button", "paypal-checkout"],
                "api_endpoints": ["/paypal/", "/api/paypal/"]
            },
            "PagSeguro": {
                "keywords": ["pagseguro.uol.com.br", "ps.uol.com.br", "pagseguro", "uol.com.br/pagseguro"],
                "scripts": ["stc.pagseguro.uol.com.br", "pagseguro.uol.com.br/resources"],
                "forms": ["pagseguro-form"],
                "meta": ["pagseguro-token"],
                "css_classes": ["pagseguro-button"],
                "api_endpoints": ["/pagseguro/", "/api/pagseguro/"]
            },
            "Mercado Pago": {
                "keywords": ["mercadopago.com", "mp.com.br", "mercadopago", "mercadolibre"],
                "scripts": ["secure.mlstatic.com/sdk/javascript/v1/mercadopago.js", "js.mercadopago.com"],
                "forms": ["mercadopago-form"],
                "meta": ["mercadopago-public-key"],
                "css_classes": ["mercadopago-button", "mp-button"],
                "api_endpoints": ["/mercadopago/", "/api/mercadopago/", "/mp/"]
            },
            "Wirecard/Moip": {
                "keywords": ["wirecard.com.br", "moip.com.br", "wirecard", "moip"],
                "scripts": ["assets.moip.com.br", "js.wirecard.com.br"],
                "forms": ["wirecard-form", "moip-form"],
                "meta": ["wirecard-key", "moip-key"],
                "css_classes": ["wirecard-button", "moip-button"],
                "api_endpoints": ["/wirecard/", "/moip/", "/api/wirecard/"]
            },
            "Pagar.me": {
                "keywords": ["pagar.me", "pagarme", "stone.com.br"],
                "scripts": ["assets.pagar.me", "js.pagar.me"],
                "forms": ["pagarme-form"],
                "meta": ["pagarme-key"],
                "css_classes": ["pagarme-button"],
                "api_endpoints": ["/pagarme/", "/api/pagarme/"]
            },
            "Ebanx": {
                "keywords": ["ebanx.com", "ebanx"],
                "scripts": ["js.ebanx.com", "checkout.ebanx.com"],
                "forms": ["ebanx-form"],
                "meta": ["ebanx-key"],
                "css_classes": ["ebanx-button"],
                "api_endpoints": ["/ebanx/", "/api/ebanx/"]
            },
            "Cielo": {
                "keywords": ["cielo.com.br", "cielo", "cieloecommerce"],
                "scripts": ["ecommerce.cielo.com.br"],
                "forms": ["cielo-form"],
                "meta": ["cielo-merchant-id"],
                "css_classes": ["cielo-button"],
                "api_endpoints": ["/cielo/", "/api/cielo/"]
            },
            "Rede": {
                "keywords": ["userede.com.br", "rede", "redecard"],
                "scripts": ["js.userede.com.br"],
                "forms": ["rede-form"],
                "meta": ["rede-key"],
                "css_classes": ["rede-button"],
                "api_endpoints": ["/rede/", "/api/rede/"]
            },
            "Getnet": {
                "keywords": ["getnet.com.br", "getnet"],
                "scripts": ["js.getnet.com.br"],
                "forms": ["getnet-form"],
                "meta": ["getnet-key"],
                "css_classes": ["getnet-button"],
                "api_endpoints": ["/getnet/", "/api/getnet/"]
            },
            "Adyen": {
                "keywords": ["adyen.com", "adyen"],
                "scripts": ["checkoutshopper-live.adyen.com", "checkoutshopper-test.adyen.com"],
                "forms": ["adyen-form"],
                "meta": ["adyen-key"],
                "css_classes": ["adyen-button"],
                "api_endpoints": ["/adyen/", "/api/adyen/"]
            },
            "Braintree": {
                "keywords": ["braintreepayments.com", "braintree", "data-braintree"],
                "scripts": ["js.braintreegateway.com", "assets.braintreegateway.com"],
                "forms": ["braintree-form"],
                "meta": ["braintree-key"],
                "css_classes": ["braintree-button"],
                "api_endpoints": ["/braintree/", "/api/braintree/"]
            },
            "Square": {
                "keywords": ["squareup.com", "square", "data-square"],
                "scripts": ["js.squareup.com", "web.squarecdn.com"],
                "forms": ["square-form"],
                "meta": ["square-application-id"],
                "css_classes": ["square-button"],
                "api_endpoints": ["/square/", "/api/square/"]
            },
            "Shopify Payments": {
                "keywords": ["shopify.com/payments", "shopify-pay", "shopifycs.com"],
                "scripts": ["cdn.shopify.com", "js.shopifycs.com"],
                "forms": ["shopify-payment-form"],
                "meta": ["shopify-checkout-api-token"],
                "css_classes": ["shopify-payment-button"],
                "api_endpoints": ["/shopify/", "/api/shopify/"]
            },
            "Authorize.Net": {
                "keywords": ["authorize.net", "authorizenet"],
                "scripts": ["js.authorize.net", "jstest.authorize.net"],
                "forms": ["authnet-form"],
                "meta": ["authnet-key"],
                "css_classes": ["authnet-button"],
                "api_endpoints": ["/authorize/", "/api/authorize/"]
            },
            "2Checkout": {
                "keywords": ["2checkout.com", "2co.com"],
                "scripts": ["www.2checkout.com/checkout/api"],
                "forms": ["twocheckout-form"],
                "meta": ["2checkout-key"],
                "css_classes": ["twocheckout-button"],
                "api_endpoints": ["/2checkout/", "/api/2checkout/"]
            },
            "Worldpay": {
                "keywords": ["worldpay.com", "worldpay"],
                "scripts": ["payments.worldpay.com"],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            },
            "Global Payments": {
                "keywords": ["globalpaymentsinc.com", "globalpayments"],
                "scripts": [],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            },
            "Ingenico": {
                "keywords": ["ingenico.com", "ingenico"],
                "scripts": [],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            },
            "Checkout.com": {
                "keywords": ["checkout.com", "checkout"],
                "scripts": ["cdn.checkout.com"],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            },
            "Klarna": {
                "keywords": ["klarna.com", "klarna"],
                "scripts": ["x.klarnacdn.net"],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            },
            "Afterpay": {
                "keywords": ["afterpay.com", "afterpay"],
                "scripts": ["static.afterpay.com"],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            },
            "Affirm": {
                "keywords": ["affirm.com", "affirm"],
                "scripts": ["cdn1.affirm.com"],
                "forms": [],
                "meta": [],
                "css_classes": [],
                "api_endpoints": []
            }
        }
        self.visited_urls = set()
        self.urls_to_visit = deque()
        self.results = []
        self.max_urls_to_crawl = 0

    def analyze_page(self, url, timeout=15, deep_analysis=False):
        """
        Analisa uma página web para detectar gateways de pagamento
        """
        try:
            logger.info(f"Analisando: {url}")
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            page_content = response.text.lower()
            
            results = {
                'url': url,
                'status_code': response.status_code,
                'gateways_found': [],
                'evidence': {},
                'confidence_scores': {},
                'analysis_time': datetime.now().isoformat(),
                'page_title': soup.title.string if soup.title else "N/A",
                'page_size': len(response.text)
            }
            
            # Análise de cada gateway
            for gateway_name, signatures in self.gateways.items():
                evidence, confidence = self._check_gateway_signatures(soup, page_content, signatures, deep_analysis)
                if evidence and confidence > 0:
                    results['gateways_found'].append(gateway_name)
                    results['evidence'][gateway_name] = evidence
                    results['confidence_scores'][gateway_name] = confidence
            
            # Análise adicional se solicitada
            if deep_analysis:
                results['additional_analysis'] = self._deep_analysis(soup, page_content)
            
            return results
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro ao acessar {url}: {e}")
            return {
                'url': url,
                'error': str(e),
                'gateways_found': [],
                'evidence': {},
                'confidence_scores': {},
                'analysis_time': datetime.now().isoformat()
            }
    
    def _check_gateway_signatures(self, soup, page_content, signatures, deep_analysis=False):
        """
        Verifica as assinaturas de um gateway específico com pontuação de confiança
        """
        evidence = []
        confidence_score = 0
        
        # Verificar palavras-chave no conteúdo (peso: 1 ponto cada)
        for keyword in signatures['keywords']:
            if keyword.lower() in page_content:
                evidence.append(f"Palavra-chave encontrada: {keyword}")
                confidence_score += 1
        
        # Verificar scripts (peso: 3 pontos cada)
        for script_src in signatures['scripts']:
            scripts = soup.find_all('script', src=True)
            for script in scripts:
                if script_src.lower() in script['src'].lower():
                    evidence.append(f"Script encontrado: {script['src']}")
                    confidence_score += 3
        
        # Verificar formulários (peso: 2 pontos cada)
        for form_class in signatures['forms']:
            forms = soup.find_all('form', class_=re.compile(form_class, re.I))
            if forms:
                evidence.append(f"Formulário encontrado: {form_class}")
                confidence_score += 2
        
        # Verificar meta tags (peso: 2 pontos cada)
        for meta_name in signatures['meta']:
            meta_tags = soup.find_all('meta', attrs={'name': re.compile(meta_name, re.I)})
            if meta_tags:
                evidence.append(f"Meta tag encontrada: {meta_name}")
                confidence_score += 2
        
        # Verificar classes CSS (peso: 1 ponto cada)
        for css_class in signatures.get('css_classes', []):
            elements = soup.find_all(class_=re.compile(css_class, re.I))
            if elements:
                evidence.append(f"Classe CSS encontrada: {css_class}")
                confidence_score += 1
        
        # Verificar endpoints de API (peso: 2 pontos cada)
        for endpoint in signatures.get('api_endpoints', []):
            if endpoint.lower() in page_content:
                evidence.append(f"Endpoint de API encontrado: {endpoint}")
                confidence_score += 2
        
        return evidence if evidence else None, confidence_score
    
    def _deep_analysis(self, soup, page_content):
        """
        Análise adicional mais profunda
        """
        analysis = {}
        
        # Verificar iframes de pagamento
        iframes = soup.find_all('iframe')
        payment_iframes = []
        for iframe in iframes:
            src = iframe.get('src', '')
            if any(keyword in src.lower() for keyword in ['payment', 'checkout', 'pay']):
                payment_iframes.append(src)
        
        if payment_iframes:
            analysis['payment_iframes'] = payment_iframes
        
        # Verificar links externos suspeitos
        external_links = []
        links = soup.find_all('a', href=True)
        for link in links:
            href = link['href']
            if any(gateway in href.lower() for gateway in ['stripe', 'paypal', 'mercadopago', 'adyen', 'braintree', 'shopify']):
                external_links.append(href)
        
        if external_links:
            analysis['external_payment_links'] = external_links
        
        # Verificar inputs de cartão de crédito
        credit_card_inputs = []
        inputs = soup.find_all('input')
        for input_tag in inputs:
            input_type = input_tag.get('type', '')
            input_name = input_tag.get('name', '')
            input_id = input_tag.get('id', '')
            
            if any(keyword in f"{input_type} {input_name} {input_id}".lower() 
                   for keyword in ['card', 'credit', 'cvv', 'expiry', 'cc-number', 'cc-exp', 'cc-csc']):
                credit_card_inputs.append({
                    'type': input_type,
                    'name': input_name,
                    'id': input_id
                })
        
        if credit_card_inputs:
            analysis['credit_card_inputs'] = credit_card_inputs
        
        return analysis
    
    def _extract_links(self, soup, base_url):
        links = set()
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            parsed_url = urlparse(full_url)
            
            # Ignorar links que não são HTTP/HTTPS
            if parsed_url.scheme not in ['http', 'https']:
                continue

            # Normalizar URL (remover fragmentos, etc.)
            clean_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path
            if clean_url.endswith('/'):
                clean_url = clean_url[:-1]
            links.add(clean_url)
        return list(links)

    def crawl_and_detect(self, seed_urls, max_depth=1, max_urls=50, max_workers=5, deep_analysis=False):
        """
        Realiza o crawling e detecção de gateways.
        """
        self.max_urls_to_crawl = max_urls
        for url in seed_urls:
            self.urls_to_visit.append((url, 0)) # (url, depth)
        
        while self.urls_to_visit and len(self.visited_urls) < self.max_urls_to_crawl:
            current_url, current_depth = self.urls_to_visit.popleft()
            
            if current_url in self.visited_urls or current_depth > max_depth:
                continue
            
            self.visited_urls.add(current_url)
            
            logger.info(f"Crawling: {current_url} (Profundidade: {current_depth}) - URLs visitadas: {len(self.visited_urls)}/{self.max_urls_to_crawl}")
            
            page_result = self.analyze_page(current_url, deep_analysis=deep_analysis)
            self.results.append(page_result)
            
            if 'error' not in page_result:
                # Extrair links para continuar o crawling
                try:
                    response = self.session.get(current_url, timeout=10)
                    soup = BeautifulSoup(response.text, 'html.parser')
                    new_links = self._extract_links(soup, current_url)
                    for link in new_links:
                        if link not in self.visited_urls and len(self.visited_urls) + len(self.urls_to_visit) < self.max_urls_to_crawl:
                            self.urls_to_visit.append((link, current_depth + 1))
                except requests.exceptions.RequestException as e:
                    logger.warning(f"Não foi possível extrair links de {current_url}: {e}")
            
            # Pequena pausa para ser educado com os servidores
            time.sleep(0.5) # Aumentado para 0.5s para ser mais gentil
        
        return self.results
    
    def export_to_csv(self, results, filename):
        """
        Exporta os resultados para CSV
        """
        with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
            fieldnames = ['url', 'gateways_found', 'confidence_total', 'status_code', 'page_title', 'error']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            
            writer.writeheader()
            for result in results:
                writer.writerow({
                    'url': result['url'],
                    'gateways_found': ', '.join(result['gateways_found']),
                    'confidence_total': sum(result.get('confidence_scores', {}).values()),
                    'status_code': result.get('status_code', 'N/A'),
                    'page_title': result.get('page_title', 'N/A'),
                    'error': result.get('error', '')
                })
        
        logger.info(f"Resultados exportados para CSV: {filename}")
    
    def generate_detailed_report(self, results, output_file=None):
        """
        Gera um relatório detalhado dos resultados
        """
        report = {
            'metadata': {
                'total_urls_analyzed': len(results),
                'urls_with_gateways': len([r for r in results if r['gateways_found']]),
                'urls_with_errors': len([r for r in results if 'error' in r]),
                'analysis_timestamp': datetime.now().isoformat(),
                'detector_version': '3.1' # Versão atualizada
            },
            'gateway_statistics': {},
            'confidence_analysis': {},
            'detailed_results': results
        }
        
        # Estatísticas por gateway
        gateway_counts = {}
        confidence_totals = {}
        
        for result in results:
            for gateway in result['gateways_found']:
                gateway_counts[gateway] = gateway_counts.get(gateway, 0) + 1
                confidence = result.get('confidence_scores', {}).get(gateway, 0)
                if gateway not in confidence_totals:
                    confidence_totals[gateway] = []
                confidence_totals[gateway].append(confidence)
        
        report['gateway_statistics'] = gateway_counts
        
        # Análise de confiança
        for gateway, confidences in confidence_totals.items():
            report['confidence_analysis'][gateway] = {
                'average_confidence': sum(confidences) / len(confidences),
                'max_confidence': max(confidences),
                'min_confidence': min(confidences),
                'total_detections': len(confidences)
            }
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)
            logger.info(f"Relatório detalhado salvo em: {output_file}")
        
        return report
    
    def print_detailed_summary(self, results):
        """
        Imprime um resumo detalhado dos resultados
        """
        print("\n" + "="*80)
        print("RELATÓRIO DETALHADO DE ANÁLISE DE GATEWAYS DE PAGAMENTO")
        print("="*80)
        
        total_urls = len(results)
        urls_with_gateways = len([r for r in results if r['gateways_found']])
        urls_with_errors = len([r for r in results if 'error' in r])
        
        print(f"📊 ESTATÍSTICAS GERAIS:")
        print(f"   Total de URLs analisadas: {total_urls}")
        print(f"   URLs com gateways encontrados: {urls_with_gateways} ({urls_with_gateways/total_urls*100:.1f}%)")
        print(f"   URLs com erros: {urls_with_errors} ({urls_with_errors/total_urls*100:.1f}%)")
        
        # Estatísticas por gateway
        gateway_counts = {}
        confidence_totals = {}
        
        for result in results:
            for gateway in result['gateways_found']:
                gateway_counts[gateway] = gateway_counts.get(gateway, 0) + 1
                confidence = result.get('confidence_scores', {}).get(gateway, 0)
                if gateway not in confidence_totals:
                    confidence_totals[gateway] = []
                confidence_totals[gateway].append(confidence)
        
        if gateway_counts:
            print(f"\n🏆 GATEWAYS MAIS ENCONTRADOS:")
            for gateway, count in sorted(gateway_counts.items(), key=lambda x: x[1], reverse=True):
                avg_confidence = sum(confidence_totals[gateway]) / len(confidence_totals[gateway])
                print(f"   {gateway}: {count} site(s) (confiança média: {avg_confidence:.1f})")
        
        print(f"\n📋 DETALHES POR URL:")
        for result in results:
            if 'error' in result:
                print(f"❌ {result['url']}")
                print(f"   ERRO: {result['error']}")
            elif result['gateways_found']:
                print(f"✅ {result['url']}")
                print(f"   Título: {result.get('page_title', 'N/A')}")
                for gateway in result['gateways_found']:
                    confidence = result.get('confidence_scores', {}).get(gateway, 0)
                    print(f"   🔍 {gateway} (confiança: {confidence})")
                    evidence = result.get('evidence', {}).get(gateway, [])
                    for ev in evidence[:3]:  # Mostrar apenas as 3 primeiras evidências
                        print(f"      • {ev}")
            else:
                print(f"⚪ {result['url']}")
                print(f"   Título: {result.get('page_title', 'N/A')}")
                print(f"   Nenhum gateway encontrado")
            print()

def load_urls_from_file(filename):
    """
    Carrega URLs de um arquivo de texto
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        return urls
    except FileNotFoundError:
        logger.error(f"Arquivo não encontrado: {filename}")
        return []

def interactive_mode():
    """
    Modo interativo para o crawler/detector
    """
    crawler = GatewayCrawlerV2()
    
    while True:
        print("\n" + "="*60)
        print("🌐 CRAWLER/DETECTOR DE GATEWAYS DE PAGAMENTO (v3.1)")
        print("="*60)
        print("1. Iniciar Crawling a partir de URLs semente")
        print("2. Analisar URL única (sem crawling)")
        print("3. Analisar URLs de arquivo (sem crawling)")
        print("4. Análise de exemplo (URLs pré-definidas, sem crawling)")
        print("5. Sair")
        
        choice = input("\nEscolha uma opção (1-5): ").strip()
        
        if choice == "1":
            seed_urls_input = input("Digite as URLs semente (separadas por vírgula): ").strip()
            seed_urls = [url.strip() for url in seed_urls_input.split(',') if url.strip()]
            
            if not seed_urls:
                print("Nenhuma URL semente fornecida.")
                continue
            
            max_depth = int(input("Profundidade máxima do crawling (padrão 1): ") or "1")
            max_urls = int(input("Número máximo de URLs para analisar (padrão 50): ") or "50")
            deep = input("Análise profunda? (s/n): ").lower().startswith('s')
            workers = int(input("Número de workers paralelos (padrão 5): ") or "5")
            
            print("Iniciando crawling e detecção...")
            results = crawler.crawl_and_detect(seed_urls, max_depth, max_urls, workers, deep)
            crawler.print_detailed_summary(results)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"relatorio_crawler_{timestamp}.json"
            csv_file = f"relatorio_crawler_{timestamp}.csv"
            crawler.generate_detailed_report(results, json_file)
            crawler.export_to_csv(results, csv_file)
            print(f"Relatórios salvos em {json_file} e {csv_file}")

        elif choice == "2":
            url = input("Digite a URL para análise: ").strip()
            if url:
                deep = input("Análise profunda? (s/n): ").lower().startswith('s')
                results = [crawler.analyze_page(url, deep_analysis=deep)]
                crawler.print_detailed_summary(results)
        
        elif choice == "3":
            filename = input("Digite o nome do arquivo com URLs: ").strip()
            urls = load_urls_from_file(filename)
            if urls:
                print(f"Carregadas {len(urls)} URLs do arquivo.")
                deep = input("Análise profunda? (s/n): ").lower().startswith('s')
                workers = int(input("Número de workers paralelos (padrão 5): ") or "5")
                results = crawler.analyze_multiple_urls(urls, max_workers=workers, deep_analysis=deep)
                crawler.print_detailed_summary(results)
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                json_file = f"relatorio_gateways_{timestamp}.json"
                csv_file = f"relatorio_gateways_{timestamp}.csv"
                crawler.generate_detailed_report(results, json_file)
                crawler.export_to_csv(results, csv_file)
                print(f"Relatórios salvos em {json_file} e {csv_file}")
        
        elif choice == "4":
            test_urls = [
                "https://stripe.com/",
                "https://www.paypal.com/",
                "https://www.mercadolivre.com.br/",
                "https://www.amazon.com.br/",
                "https://www.shopify.com/",
                "https://www.google.com/",
                "https://www.netflix.com/"
            ]
            
            print(f"Analisando {len(test_urls)} URLs de exemplo...")
            results = crawler.analyze_multiple_urls(test_urls, deep_analysis=True)
            crawler.print_detailed_summary(results)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            json_file = f"relatorio_exemplo_{timestamp}.json"
            csv_file = f"relatorio_exemplo_{timestamp}.csv"
            crawler.generate_detailed_report(results, json_file)
            crawler.export_to_csv(results, csv_file)
            print(f"Relatórios salvos em {json_file} e {csv_file}")
        
        elif choice == "5":
            print("Encerrando o crawler/detector...")
            break
        
        else:
            print("Opção inválida. Tente novamente.")

def main():
    parser = argparse.ArgumentParser(description='Crawler/Detector Avançado de Gateways de Pagamento')
    parser.add_argument('--url', help='URL única para análise (sem crawling)')
    parser.add_argument('--file', help='Arquivo com lista de URLs para análise (sem crawling)')
    parser.add_argument('--seed_urls', help='URLs semente para iniciar o crawling (separadas por vírgula)')
    parser.add_argument('--max_depth', type=int, default=1, help='Profundidade máxima do crawling')
    parser.add_argument('--max_urls', type=int, default=50, help='Número máximo de URLs para analisar no crawling')
    parser.add_argument('--output', help='Arquivo de saída para o relatório JSON')
    parser.add_argument('--csv', help='Arquivo de saída para o relatório CSV')
    parser.add_argument('--deep', action='store_true', help='Ativar análise profunda')
    parser.add_argument('--workers', type=int, default=5, help='Número de workers paralelos')
    parser.add_argument('--interactive', action='store_true', help='Modo interativo')
    
    args = parser.parse_args()
    
    if args.interactive or len(sys.argv) == 1:
        interactive_mode()
        return
    
    crawler = GatewayCrawlerV2()
    
    if args.seed_urls:
        seed_urls_list = [url.strip() for url in args.seed_urls.split(',') if url.strip()]
        results = crawler.crawl_and_detect(seed_urls_list, args.max_depth, args.max_urls, args.workers, args.deep)
    elif args.url:
        results = [crawler.analyze_page(args.url, deep_analysis=args.deep)]
    elif args.file:
        urls = load_urls_from_file(args.file)
        if not urls:
            return
        results = crawler.analyze_multiple_urls(urls, max_workers=args.workers, deep_analysis=args.deep)
    else:
        print("Especifique --url, --file, --seed_urls ou use --interactive")
        return
    
    crawler.print_detailed_summary(results)
    
    if args.output:
        crawler.generate_detailed_report(results, args.output)
    
    if args.csv:
        crawler.export_to_csv(results, args.csv)

if __name__ == "__main__":
    main()

