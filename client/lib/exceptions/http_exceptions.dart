import 'dart:io';

class HttpCodedException extends HttpException {
  final int statusCode;

  HttpCodedException({
    required this.statusCode,
    required String message,
    Uri? uri,
  }) : super(message, uri: uri);

  @override
  String toString() {
    return "Error $statusCode: ${super.toString()}";
  }
}

class JsonResponseMismatchException
    extends ResponseMismatchException<Map<String, dynamic>> {
  JsonResponseMismatchException(
    super.expected,
    super.actual, {
    super.message = "",
  });
}

class ResponseMismatchException<T> implements Exception {
  final T expected;
  final T actual;
  final String message;

  ResponseMismatchException(this.expected, this.actual, {this.message = ""});

  @override
  String toString() {
    if (message.isNotEmpty) {
      return message;
    }
    return "Expected: $expected\nActual: $actual";
  }
}

class InvalidUrlException implements Exception {
  final String message;

  InvalidUrlException(this.message);

  @override
  String toString() => message;
}

class HttpClientException implements Exception {
  final String message;
  final Object? inner;

  const HttpClientException(this.message, {this.inner});

  @override
  String toString() => message;
}

class FailedToConnectException implements Exception {
  final String message;

  const FailedToConnectException(this.message);

  @override
  String toString() => message;
}
