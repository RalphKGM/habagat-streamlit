from habagat import mapview, theme

theme.html(
    """<style>
    [data-testid="stMainBlockContainer"] { max-width:none; padding:3.6rem 1rem .5rem; }
    </style>"""
)
mapview.render()
