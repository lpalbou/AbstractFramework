"""
AbstractFramework - A unified ecosystem for AI-powered applications and intelligent systems.

This is the main entry point for the AbstractFramework ecosystem, which includes:
- AbstractCore: Unified LLM provider interface
- AbstractMemory: Advanced memory systems (coming soon)
- AbstractAgent: Intelligent agent framework (coming soon)  
- AbstractSwarm: Multi-agent coordination (coming soon)

Example:
    >>> import abstractframework as af
    >>> # When all components are available:
    >>> agent = af.create_agent(llm_provider="openai", model="gpt-4o-mini")
    >>> response = agent.chat("Hello, world!")
"""

__version__ = "0.1.0"
__author__ = "Laurent-Philippe Albou"
__email__ = "lpalbou@gmail.com"
__description__ = "A unified ecosystem for AI-powered applications and intelligent systems"
__url__ = "https://github.com/lpalbou/AbstractFramework"

# Component availability flags
ABSTRACTCORE_AVAILABLE = False
ABSTRACTMEMORY_AVAILABLE = False
ABSTRACTAGENT_AVAILABLE = False
ABSTRACTSWARM_AVAILABLE = False

# Try to import available components
try:
    import abstractcore
    ABSTRACTCORE_AVAILABLE = True
    __all__ = ["abstractcore"]
except ImportError:
    __all__ = []

try:
    import abstractmemory
    ABSTRACTMEMORY_AVAILABLE = True
    __all__.append("abstractmemory")
except ImportError:
    pass

try:
    import abstractagent
    ABSTRACTAGENT_AVAILABLE = True
    __all__.append("abstractagent")
except ImportError:
    pass

try:
    import abstractswarm
    ABSTRACTSWARM_AVAILABLE = True
    __all__.append("abstractswarm")
except ImportError:
    pass


def get_available_components():
    """
    Get a list of currently available AbstractFramework components.
    
    Returns:
        dict: Dictionary mapping component names to their availability status
    """
    return {
        "abstractcore": ABSTRACTCORE_AVAILABLE,
        "abstractmemory": ABSTRACTMEMORY_AVAILABLE,
        "abstractagent": ABSTRACTAGENT_AVAILABLE,
        "abstractswarm": ABSTRACTSWARM_AVAILABLE,
    }


def get_version_info():
    """
    Get version information for AbstractFramework and its components.
    
    Returns:
        dict: Dictionary with version information for each component
    """
    versions = {"abstractframework": __version__}
    
    if ABSTRACTCORE_AVAILABLE:
        try:
            versions["abstractcore"] = abstractcore.__version__
        except AttributeError:
            versions["abstractcore"] = "unknown"
    
    if ABSTRACTMEMORY_AVAILABLE:
        try:
            versions["abstractmemory"] = abstractmemory.__version__
        except AttributeError:
            versions["abstractmemory"] = "unknown"
    
    if ABSTRACTAGENT_AVAILABLE:
        try:
            versions["abstractagent"] = abstractagent.__version__
        except AttributeError:
            versions["abstractagent"] = "unknown"
    
    if ABSTRACTSWARM_AVAILABLE:
        try:
            versions["abstractswarm"] = abstractswarm.__version__
        except AttributeError:
            versions["abstractswarm"] = "unknown"
    
    return versions


# Placeholder functions for future unified API
def create_agent(*args, **kwargs):
    """
    Create an intelligent agent (placeholder - requires AbstractAgent).
    
    This function will be available when AbstractAgent is released.
    Currently raises NotImplementedError.
    
    Raises:
        NotImplementedError: AbstractAgent is not yet available
    """
    if not ABSTRACTAGENT_AVAILABLE:
        raise NotImplementedError(
            "AbstractAgent is not yet available. "
            "This function will be implemented when AbstractAgent is released. "
            "For now, use AbstractCore directly: pip install abstractcore[all]"
        )
    
    # Future implementation will delegate to AbstractAgent
    return abstractagent.create_agent(*args, **kwargs)


def create_swarm(*args, **kwargs):
    """
    Create a multi-agent swarm (placeholder - requires AbstractSwarm).
    
    This function will be available when AbstractSwarm is released.
    Currently raises NotImplementedError.
    
    Raises:
        NotImplementedError: AbstractSwarm is not yet available
    """
    if not ABSTRACTSWARM_AVAILABLE:
        raise NotImplementedError(
            "AbstractSwarm is not yet available. "
            "This function will be implemented when AbstractSwarm is released."
        )
    
    # Future implementation will delegate to AbstractSwarm
    return abstractswarm.create_swarm(*args, **kwargs)


def create_memory(*args, **kwargs):
    """
    Create a memory system (placeholder - requires AbstractMemory).
    
    This function will be available when AbstractMemory is released.
    Currently raises NotImplementedError.
    
    Raises:
        NotImplementedError: AbstractMemory is not yet available
    """
    if not ABSTRACTMEMORY_AVAILABLE:
        raise NotImplementedError(
            "AbstractMemory is not yet available. "
            "This function will be implemented when AbstractMemory is released."
        )
    
    # Future implementation will delegate to AbstractMemory
    return abstractmemory.create_memory(*args, **kwargs)


# Convenience function to check framework status
def status():
    """
    Print the current status of AbstractFramework components.
    """
    print("AbstractFramework Status:")
    print(f"  Version: {__version__}")
    print("\nComponent Availability:")
    
    components = get_available_components()
    for component, available in components.items():
        status_icon = "✅" if available else "❌"
        status_text = "Available" if available else "Not Available"
        print(f"  {status_icon} {component}: {status_text}")
    
    if ABSTRACTCORE_AVAILABLE:
        print(f"\nTo get started with AbstractCore:")
        print(f"  from abstractcore import create_llm")
        print(f"  llm = create_llm('openai', model='gpt-4o-mini')")
        print(f"  response = llm.generate('Hello, world!')")
    else:
        print(f"\nTo install AbstractCore:")
        print(f"  pip install abstractcore[all]")
    
    print(f"\nFor more information: {__url__}")


# Make status available at package level
__all__.extend(["get_available_components", "get_version_info", "status", 
                "create_agent", "create_swarm", "create_memory"])
