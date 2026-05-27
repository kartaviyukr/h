import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  runApp(const ProviderScope(child: NeuromarketApp()));
}

class NeuromarketApp extends StatelessWidget {
  const NeuromarketApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Neuromarket',
      theme: ThemeData(useMaterial3: true, colorSchemeSeed: Colors.green),
      home: const HomeScreen(),
    );
  }
}

class HomeScreen extends StatelessWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return const Scaffold(
      body: Center(
        child: Text('Hello', style: TextStyle(fontSize: 32)),
      ),
    );
  }
}
