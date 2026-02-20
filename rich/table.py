class Table:
    def __init__(self, title=None):
        self.title = title
        self.columns = []
        self.rows = []

    def add_column(self, name, style=None):
        self.columns.append((name, style))

    def add_row(self, *cells):
        self.rows.append(cells)

    def __repr__(self):
        return f"Table(title={self.title}, columns={self.columns}, rows={self.rows})"
