#ifndef __CFACTORY_H__
#define __CFACTORY_H__
#include <CStrategy.h>

class CFactory
{
public:
  static CStrategy* makeStrategy(const std::string& strategyName);
};

#endif
