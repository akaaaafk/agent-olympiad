"""Bounded scalar comparison with explicit units and sourced tolerances.

No expression evaluation, implicit dimensional coercion, or default tolerance.
"""
from decimal import Decimal, DecimalException, localcontext
from fractions import Fraction
import re

from .final_answer import extract_final_answer
from .models import EvaluationError

D = Decimal
# dimension, SI scale, SI offset. Absolute temperatures and angles have their own dimensions.
UNITS = {
    '': ('scalar','1','0'), '1': ('scalar','1','0'), '%': ('scalar','0.01','0'),
    'm': ('length','1','0'), 'km': ('length','1000','0'), 'cm': ('length','0.01','0'),
    'mm': ('length','0.001','0'), 'um': ('length','0.000001','0'), 'nm': ('length','1e-9','0'),
    's': ('time','1','0'), 'min': ('time','60','0'), 'h': ('time','3600','0'),
    'kg': ('mass','1','0'), 'g': ('mass','0.001','0'),
    'm/s': ('speed','1','0'), 'km/h': ('speed','5/18','0'),
    'm/s^2': ('acceleration','1','0'), 'cm/s^2': ('acceleration','0.01','0'),
    'm^2': ('area','1','0'), 'cm^2': ('area','0.0001','0'),
    'm^3': ('volume','1','0'), 'cm^3': ('volume','0.000001','0'), 'L': ('volume','0.001','0'),
    'rad': ('angle','1','0'), 'deg': ('angle','0.017453292519943295769236907684886','0'),
    'K': ('temperature','1','0'), 'degC': ('temperature','1','273.15'),
    'N': ('force','1','0'), 'J': ('energy','1','0'), 'kJ': ('energy','1000','0'),
    'W': ('power','1','0'), 'kW': ('power','1000','0'),
    'Pa': ('pressure','1','0'), 'kPa': ('pressure','1000','0'), 'MPa': ('pressure','1000000','0'),
    'Hz': ('frequency','1','0'), 'kHz': ('frequency','1000','0'),
}
NUMBER = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][+-]?\d{1,3})?'


def unit_name(text):
    text = re.sub(r'\\(?:mathrm|text)\{([^{}]*)\}', r'\1', text)
    text = text.replace('μ','u').replace('µ','u').replace('²','^2').replace('³','^3')
    text = text.replace('°C','degC').replace('°','deg').replace('·','*').replace('−','-')
    text = re.sub(r'\s+','',text)
    return {'m*s^-1':'m/s','ms^-1':'m/s','m*s^-2':'m/s^2','ms^-2':'m/s^2',
            'radians':'rad','radian':'rad','degrees':'deg','degree':'deg'}.get(text,text)


def number(text):
    text = str(text)
    if len(text)>128 or not re.fullmatch(NUMBER,text):
        raise ValueError('Expected a finite decimal/scientific scalar')
    value=D(text)
    if not value.is_finite() or abs(value.adjusted())>300:
        raise ValueError('Scalar outside supported range')
    return value


def validate_spec(spec):
    try:
        expected=number(spec['value']); absolute=number(spec['abs_tol']); relative=number(spec['rel_tol'])
        unit=unit_name(spec['unit'])
        if unit not in UNITS or absolute<0 or relative<0 or not spec.get('tolerance_basis'):
            raise ValueError('Unsupported unit, negative tolerance, or missing tolerance provenance')
        if type(spec.get('allow_implicit_unit',False)) is not bool:
            raise ValueError('allow_implicit_unit must be boolean')
        return expected,absolute,relative,unit
    except (KeyError,ValueError,TypeError,DecimalException) as exc:
        raise EvaluationError('Invalid numeric gold specification: '+str(exc)) from exc


def compare_numeric(spec, actual):
    expected,absolute,relative,expected_unit=validate_spec(spec)
    selected=extract_final_answer(str(actual)).final_answer.strip().strip('$').replace('−','-')
    selected=selected.replace(r'\,',' ').replace(r'\!','')
    selected=re.sub(r'([\d.]+)\s*(?:×|\*|x|\\times)\s*10\s*\^\s*\{?([+-]?\d+)\}?',r'\1e\2',selected)
    match=re.fullmatch(r'('+NUMBER+r')\s*(.*)',selected)
    if not match:return {'correct':False,'reason':'not_a_single_numeric_answer'}
    try:
        value=number(match[1]); actual_unit=unit_name(match[2])
        if not actual_unit and expected_unit:
            if not spec.get('allow_implicit_unit',False):return {'correct':False,'reason':'missing_unit'}
            actual_unit=expected_unit
        if actual_unit not in UNITS:return {'correct':False,'reason':'unsupported_unit_or_trailing_text'}
        dim,scale,offset=UNITS[actual_unit]; target_dim,target_scale,target_offset=UNITS[expected_unit]
        if dim!=target_dim:return {'correct':False,'reason':'incompatible_units'}
        with localcontext() as context:
            context.prec=50
            converted=(Fraction(value)*Fraction(scale)+Fraction(offset)-Fraction(target_offset))/Fraction(target_scale)
            error=abs(converted-Fraction(expected)); tolerance=Fraction(max(absolute,relative*abs(expected)))
            return dict(correct=error<=tolerance,reason='within_tolerance' if error<=tolerance else 'outside_tolerance',
                        converted_value=str(converted),expected_unit=expected_unit,error=str(error),tolerance=str(tolerance))
    except (ValueError,DecimalException):
        return {'correct':False,'reason':'invalid_numeric_value'}
