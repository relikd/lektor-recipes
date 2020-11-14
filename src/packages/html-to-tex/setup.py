from setuptools import setup

setup(
    name='lektor-html-to-tex',
    py_modules=['lektor_html-to-tex'],
    version='1.0',
    entry_points={
        'lektor.plugins': [
            'html-to-tex = lektor_html_to_tex:HtmlToTex',
        ]
    }
)
