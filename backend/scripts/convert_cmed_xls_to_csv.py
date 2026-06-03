import pandas as pd
import sys

def clean_and_convert_cmed_file(input_filepath: str, output_filepath: str) -> None:
    try:
        print("Lendo o arquivo XLSX...")
        df = pd.read_excel(input_filepath, sheet_name='Planilha1', skiprows=41)
        
        df.dropna(how='all', axis=1, inplace=True)
        
        print("Exportando CSV em UTF-8...")
        # A exportação em UTF-8 garante a preservação de 100% dos caracteres originais
        df.to_csv(output_filepath, sep=';', encoding='utf-8', index=False)
        
        print(f"Sucesso! Arquivo pronto salvo em: {output_filepath}")
        
    except Exception as e:
        print(f"Falha fatal no processamento: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python convert_cmed_xls_to_csv.py <caminho_entrada.xlsx> <caminho_saida.csv>")
        sys.exit(1)
        
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    clean_and_convert_cmed_file(input_file, output_file)