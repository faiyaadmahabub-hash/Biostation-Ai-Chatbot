"""
Unit tests for R error parser
"""
import pytest
from app.debugger import RErrorParser, error_parser


class TestRErrorParser:
    """Test RErrorParser functionality"""

    def test_parse_object_not_found(self):
        """Test parsing 'object not found' error"""
        error_msg = "Error in eval(expr, envir, enclos) : object 'mydata' not found"

        result = error_parser.parse(error_msg)

        assert result.error_type == "object_not_found"
        assert "mydata" in result.details
        assert len(result.suggestions) > 0

    def test_parse_column_not_found(self):
        """Test parsing column not found error"""
        error_msg = "Error in `$<-.data.frame`(`*tmp*`, col, value = c(1, 2)) : replacement has 2 rows, data has 3"

        result = error_parser.parse(error_msg)

        assert result.error_type is not None
        assert result.severity in ["error", "warning"]

    def test_parse_non_numeric(self):
        """Test parsing non-numeric argument error"""
        error_msg = "Error in mean.default(X[[i]], ...) : argument is not numeric or logical: returning NA"

        result = error_parser.parse(error_msg)

        assert result.error_type == "non_numeric"
        assert len(result.suggestions) > 0

    def test_unknown_error(self):
        """Test handling of unknown error types"""
        error_msg = "Some random R error message"

        result = error_parser.parse(error_msg)

        assert result.error_type == "unknown"
        assert result.message == error_msg
