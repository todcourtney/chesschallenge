////////////////////////////////////////////////////////////
// Add all C++ strategies here:
// 1) as a #include, and
// 2) mapping a string name to the class constructor
////////////////////////////////////////////////////////////

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
