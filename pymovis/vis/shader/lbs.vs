#version 430
#define MAX_JOINT_NUM 100
uniform mat4 uLbsJoints[MAX_JOINT_NUM];

// --------------------------------------------
// input vertex data
// --------------------------------------------
layout(location=0) in vec3  vPosition;
layout(location=1) in vec3  vNormal;
layout(location=2) in vec2  vTexCoord;
layout(location=3) in int   vMaterialID;
layout(location=4) in ivec4 vLbsJointIDs1;
layout(location=5) in vec4  vLbsWeights1;
layout(location=6) in ivec4 vLbsJointIDs2;
layout(location=7) in vec4  vLbsWeights2;

// --------------------------------------------
// output vertex data
// --------------------------------------------
out vec3 fPosition;
out vec3 fNormal;
out vec2 fTexCoord;
flat out int  fMaterialID;
out vec4 fPosLightSpace;

// --------------------------------------------
// uniform data
// --------------------------------------------
uniform mat4 P;
uniform mat4 V;
uniform mat4 lightSpaceMatrix;

mat4 GetJointMatrix(ivec4 ids, vec4 weights)
{
    mat4 m = mat4(0.0f);
    if (0 <= ids.x && ids.x < MAX_JOINT_NUM)
    {
        m += uLbsJoints[ids.x] * weights.x;
    }
    if (0 <= ids.y && ids.y < MAX_JOINT_NUM)
    {
        m += uLbsJoints[ids.y] * weights.y;
    }
    if (0 <= ids.z && ids.z < MAX_JOINT_NUM)
    {
        m += uLbsJoints[ids.z] * weights.z;
    }
    if (0 <= ids.w && ids.w < MAX_JOINT_NUM)
    {
        m += uLbsJoints[ids.w] * weights.w;
    }
    return m;
}

void main()
{
    // LBS
    mat4 lbsModel1 = GetJointMatrix(vLbsJointIDs1, vLbsWeights1);
    mat4 lbsModel2 = GetJointMatrix(vLbsJointIDs2, vLbsWeights2);
    mat4 modelLBS  = lbsModel1 + lbsModel2;

    fPosition      = vec3(modelLBS * vec4(vPosition, 1.0));
    fNormal        = normalize(transpose(inverse(mat3(modelLBS))) * vNormal);
    fTexCoord      = vTexCoord;
    fPosLightSpace = lightSpaceMatrix * vec4(fPosition, 1.0);
    fMaterialID    = vMaterialID;

    gl_Position    = P * V * vec4(fPosition, 1.0);
}