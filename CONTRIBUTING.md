# Guía de contribución — gm-backend

## Ramas

- `main`: producción. Solo recibe merges desde la rama de cada desarrollador
- `desarrollador1`: rama de cada desarrollador. 

## Formato de commits (Conventional Commits)

```
tipo(módulo): descripción corta en presente

feat(songs): agregar endpoint de generación de canción
fix(auth): corregir validación de token expirado
refactor(credits): extraer lógica de descuento a service
test(users): agregar tests de registro
docs(readme): actualizar instrucciones de setup
chore(deps): actualizar django a 5.0.3
```

## Estándar de código Python (PEP 8)

- Nombres de variables y funciones: `snake_case`
- Nombres de clases: `PascalCase`
- Máximo 88 caracteres por línea (Black formatter)
- Toda función pública con docstring de una línea mínimo
- Sin `import *`
- Imports ordenados: stdlib → third-party → local

## Lógica en services, no en views

Las views solo:
1. Reciben la request
2. Validan con el serializer
3. Llaman al service
4. Devuelven la response

Nunca queries complejas ni lógica de negocio directamente en views.