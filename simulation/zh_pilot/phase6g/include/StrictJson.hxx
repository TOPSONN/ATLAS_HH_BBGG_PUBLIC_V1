#pragma once
// Small strict JSON reader for hash-bound local authorization receipts.
// No permissive comments, duplicate keys, nonfinite numbers or trailing bytes.
#include <cctype>
#include <map>
#include <stdexcept>
#include <string>
#include <vector>

namespace zh {
struct Json {
  enum Kind { Null, Boolean, Number, String, Object, Array } kind = Null;
  std::string text;
  std::map<std::string,Json> object;
  std::vector<Json> array;
  const Json& at(const std::string& key) const {
    if(kind != Object || !object.count(key)) throw std::runtime_error("Missing JSON key: " + key);
    return object.at(key);
  }
  std::string string() const {
    if(kind != String) throw std::runtime_error("Require JSON string");
    return text;
  }
  long integer() const {
    if(kind != Number || text.find_first_of(".eE") != std::string::npos) throw std::runtime_error("Require JSON integer");
    std::size_t end=0; long value=std::stol(text,&end);
    if(end != text.size()) throw std::runtime_error("Invalid JSON integer");
    return value;
  }
  double number() const {
    if(kind != Number) throw std::runtime_error("Require JSON number");
    return std::stod(text);
  }
};
class JsonParser {
  const std::string& data_; std::size_t pos_=0;
  void need(bool condition,const char* reason) const {if(!condition) throw std::runtime_error(reason);}
  void space(){while(pos_<data_.size() && (data_[pos_]==' '||data_[pos_]=='\n'||data_[pos_]=='\r'||data_[pos_]=='\t')) ++pos_;}
  char take(){need(pos_<data_.size(),"Truncated JSON");return data_[pos_++];}
  std::string string(){
    need(take()=='"',"Require quoted JSON key/string");std::string value;
    for(;;){unsigned char c=take();if(c=='"')break;need(c>=32,"Control byte in JSON string");
      if(c!='\\'){value+=char(c);continue;}
      char escape=take();
      if(escape=='"'||escape=='\\'||escape=='/')value+=escape;
      else if(escape=='b')value+='\b';else if(escape=='f')value+='\f';
      else if(escape=='n')value+='\n';else if(escape=='r')value+='\r';else if(escape=='t')value+='\t';
      else if(escape=='u'){
        unsigned int code=0;
        for(int i=0;i<4;++i){char h=take();int digit=(h>='0'&&h<='9')?h-'0':(h>='a'&&h<='f')?h-'a'+10:(h>='A'&&h<='F')?h-'A'+10:-1;
          need(digit>=0,"Invalid Unicode escape");code=code*16+digit;}
        need(code<0xd800||code>0xdfff,"Surrogate Unicode escape unsupported in authorization receipt");
        if(code<128)value+=char(code);
        else if(code<2048){value+=char(0xc0|(code>>6));value+=char(0x80|(code&63));}
        else{value+=char(0xe0|(code>>12));value+=char(0x80|((code>>6)&63));value+=char(0x80|(code&63));}
      }else throw std::runtime_error("Unknown JSON string escape");
    }return value;
  }
  Json value(int depth){
    need(depth<32,"JSON nesting exceeds bound");space();need(pos_<data_.size(),"Missing JSON value");Json result;
    char c=data_[pos_];
    if(c=='"'){result.kind=Json::String;result.text=string();return result;}
    if(c=='{'||c=='['){bool obj=c=='{';result.kind=obj?Json::Object:Json::Array;++pos_;space();
      char finish=obj?'}':']';if(pos_<data_.size()&&data_[pos_]==finish){++pos_;return result;}
      for(;;){space();if(obj){std::string key=string();space();need(take()==':',"Missing JSON colon");
          need(!result.object.count(key),"Duplicate JSON key");result.object.emplace(key,value(depth+1));}
        else result.array.push_back(value(depth+1));
        space();char separator=take();if(separator==finish)break;need(separator==',',"Missing JSON comma");}
      return result;
    }
    for(const std::string& token:{std::string("true"),std::string("false"),std::string("null")})
      if(data_.compare(pos_,token.size(),token)==0){pos_+=token.size();result.kind=token=="null"?Json::Null:Json::Boolean;result.text=token;return result;}
    std::size_t begin=pos_;if(c=='-')++pos_;
    need(pos_<data_.size()&&std::isdigit(static_cast<unsigned char>(data_[pos_])),"Invalid JSON number/value");
    if(data_[pos_]=='0')++pos_;else while(pos_<data_.size()&&std::isdigit(static_cast<unsigned char>(data_[pos_])))++pos_;
    if(pos_<data_.size()&&data_[pos_]=='.'){++pos_;std::size_t start=pos_;while(pos_<data_.size()&&std::isdigit(static_cast<unsigned char>(data_[pos_])))++pos_;need(pos_>start,"Missing fractional digits");}
    if(pos_<data_.size()&&(data_[pos_]=='e'||data_[pos_]=='E')){++pos_;if(pos_<data_.size()&&(data_[pos_]=='+'||data_[pos_]=='-'))++pos_;
      std::size_t start=pos_;while(pos_<data_.size()&&std::isdigit(static_cast<unsigned char>(data_[pos_])))++pos_;need(pos_>start,"Missing exponent digits");}
    result.kind=Json::Number;result.text=data_.substr(begin,pos_-begin);return result;
  }
public:
  explicit JsonParser(const std::string& data):data_(data){}
  Json parse(){auto result=value(0);space();need(pos_==data_.size(),"Trailing JSON data");return result;}
};
inline Json parse_json(const std::string& data){return JsonParser(data).parse();}
}
