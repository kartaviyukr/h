import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'package:neuromarket/main.dart';

void main() {
  testWidgets('shows Hello text', (tester) async {
    await tester.pumpWidget(const ProviderScope(child: NeuromarketApp()));

    expect(find.text('Hello'), findsOneWidget);
  });
}
