"""エクスポートサービス。

このモジュールは、レポートデータのエクスポート機能を提供します。
"""

import csv
import io

from openpyxl import Workbook


class ExportService:
    """エクスポートサービス。"""

    @staticmethod
    def create_csv(headers: list[str], rows: list[list[str]]) -> io.StringIO:
        """CSVファイルを作成する。

        Args:
            headers: ヘッダー行。
            rows: データ行のリスト。

        Returns:
            io.StringIO: CSV形式の文字列ストリーム。
        """
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        return output

    @staticmethod
    def create_excel(headers: list[str], rows: list[list[str]]) -> io.BytesIO:
        """Excelファイルを作成する。

        Args:
            headers: ヘッダー行。
            rows: データ行のリスト。

        Returns:
            io.BytesIO: Excelファイルのバイトストリーム。
        """
        wb = Workbook()
        ws = wb.active
        assert ws is not None  # type narrowing
        ws.title = '生成結果'

        ws.append(headers)
        for row in rows:
            ws.append(row)

        output = io.BytesIO()
        wb.save(output)
        output.seek(0)
        return output
