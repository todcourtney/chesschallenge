#include "CFactory.h"
#include "MaterialCountStrategy.h"
#include <stdexcept>

CStrategy* CFactory::makeStrategy(const std::string& strategyName)
{
  if (strategyName == "MaterialCountStrategy")
    return new MaterialCountStrategy();
  else
    throw std::runtime_error("Unknown strategy type");
}
