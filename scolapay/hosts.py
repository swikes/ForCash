"""
Adresses ajoutées automatiquement quand l'application tourne sur une
plateforme connue : GitHub Codespaces (essai sans installation) ou Render
(démo en ligne). Ailleurs, on utilise DJANGO_ALLOWED_HOSTS.
"""

CODESPACES_PORT = 8000


def platform_hosts(environ):
    """Renvoie (noms d'hôte autorisés, origines HTTPS de confiance) détectés."""
    hosts, origins = [], []
    codespace = environ.get("CODESPACE_NAME")
    forwarding_domain = environ.get("GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN")
    if codespace and forwarding_domain:
        hosts.append(f"{codespace}-{CODESPACES_PORT}.{forwarding_domain}")
    render_host = environ.get("RENDER_EXTERNAL_HOSTNAME")
    if render_host:
        hosts.append(render_host)
    origins = [f"https://{host}" for host in hosts]
    return hosts, origins
